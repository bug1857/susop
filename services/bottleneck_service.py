import pandas as pd
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.repositories.process_bottleneck_repository import ProcessBottleneckRepository
from app.models.models import ProcessBottleneck

class BottleneckService:
    def __init__(self, db: Session):
        self.db = db
        self.bottleneck_repo = ProcessBottleneckRepository(db)

    def generate_and_save_bottlenecks(
        self,
        df: pd.DataFrame,
        analysis_id: UUID,
        tenant_id: UUID,
        workspace_id: UUID,
        project_id: UUID
    ) -> List[ProcessBottleneck]:
        # Sort chronologically
        df_sorted = df.sort_values(by=["case:concept:name", "time:timestamp"])
        
        # Calculate transition time to previous event per case
        df_sorted["prev_timestamp"] = df_sorted.groupby("case:concept:name")["time:timestamp"].shift(1)
        df_sorted["prev_activity"] = df_sorted.groupby("case:concept:name")["concept:name"].shift(1)
        
        # Transition wait time in seconds
        df_sorted["wait_time_sec"] = (df_sorted["time:timestamp"] - df_sorted["prev_timestamp"]).dt.total_seconds()
        
        # Filter out first events
        df_transitions = df_sorted[df_sorted["wait_time_sec"].notnull()]
        
        if df_transitions.empty:
            return []
            
        # Group by target activity
        activity_stats = df_transitions.groupby("concept:name").agg(
            avg_wait=("wait_time_sec", "mean"),
            cnt=("wait_time_sec", "count")
        )
        
        bottlenecks = []
        for activity, row in activity_stats.iterrows():
            avg_wait_time = float(row["avg_wait"])
            count = int(row["cnt"])
            
            # Find the slowest transition leading to this activity
            act_df = df_transitions[df_transitions["concept:name"] == activity]
            slowest_row = None
            if not act_df.empty:
                idx_max = act_df["wait_time_sec"].idxmax()
                slowest_row = act_df.loc[idx_max]
            
            meta = {}
            if slowest_row is not None:
                meta["slowest_transition_from"] = str(slowest_row["prev_activity"])
                meta["longest_wait_seconds"] = float(slowest_row["wait_time_sec"])
                
            # Check for loops (activity repeated in same case)
            loops_count = 0
            for name, group in df_sorted.groupby("case:concept:name"):
                act_counts = group["concept:name"].value_counts()
                if activity in act_counts and act_counts[activity] > 1:
                    loops_count += int(act_counts[activity] - 1)
            meta["activity_loop_repeats"] = loops_count
            
            pb = ProcessBottleneck(
                analysis_id=analysis_id,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                project_id=project_id,
                activity_name=str(activity),
                average_wait_time=avg_wait_time,
                occurrence_count=count,
                metadata_fields=meta,
                is_deleted=False
            )
            bottlenecks.append(self.bottleneck_repo.create(pb))
            
        return bottlenecks

    def get_bottlenecks(self, analysis_id: UUID, tenant_id: UUID) -> List[ProcessBottleneck]:
        return self.bottleneck_repo.get_by_analysis(analysis_id, tenant_id)
