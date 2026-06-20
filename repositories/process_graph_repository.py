from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.models.models import ProcessGraph

class ProcessGraphRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[ProcessGraph]:
        return self.db.query(ProcessGraph).filter(
            ProcessGraph.analysis_id == analysis_id,
            ProcessGraph.tenant_id == tenant_id,
            ProcessGraph.is_deleted == False
        ).all()

    def create(self, graph: ProcessGraph) -> ProcessGraph:
        self.db.add(graph)
        self.db.commit()
        self.db.refresh(graph)
        return graph
