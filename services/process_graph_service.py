import pandas as pd
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.repositories.process_graph_repository import ProcessGraphRepository
from app.models.models import ProcessGraph

class ProcessGraphService:
    def __init__(self, db: Session):
        self.db = db
        self.graph_repo = ProcessGraphRepository(db)

    def generate_and_save_graphs(
        self,
        df: pd.DataFrame,
        analysis_id: UUID,
        tenant_id: UUID,
        workspace_id: UUID,
        project_id: UUID
    ) -> List[ProcessGraph]:
        # Sort chronologically per case
        df_sorted = df.sort_values(by=["case:concept:name", "time:timestamp"])
        
        # Get unique activities as nodes
        unique_activities = df_sorted["concept:name"].unique().tolist()
        nodes = [{"id": act, "label": act} for act in unique_activities]
        
        # Get shifts to construct transitions
        df_sorted["prev_activity"] = df_sorted.groupby("case:concept:name")["concept:name"].shift(1)
        df_transitions = df_sorted[df_sorted["prev_activity"].notnull()]
        
        # Count frequencies of transitions
        transition_counts = df_transitions.groupby(["prev_activity", "concept:name"]).size().reset_index(name="frequency")
        
        edges = []
        for _, row in transition_counts.iterrows():
            edges.append({
                "source": str(row["prev_activity"]),
                "target": str(row["concept:name"]),
                "frequency": int(row["frequency"])
            })
            
        graph_data = {
            "nodes": nodes,
            "edges": edges
        }
        
        pg = ProcessGraph(
            analysis_id=analysis_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            graph_type="dfg",
            node_count=len(nodes),
            edge_count=len(edges),
            graph_data=graph_data,
            is_deleted=False
        )
        
        saved_graph = self.graph_repo.create(pg)
        return [saved_graph]

    def get_graphs(self, analysis_id: UUID, tenant_id: UUID) -> List[ProcessGraph]:
        return self.graph_repo.get_by_analysis(analysis_id, tenant_id)
