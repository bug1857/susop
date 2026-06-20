from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import AiExplainability

class AiExplainabilityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, explanation: AiExplainability) -> AiExplainability:
        self.db.add(explanation)
        self.db.commit()
        self.db.refresh(explanation)
        return explanation

    def get_by_entity(self, tenant_id: UUID, entity_type: str, entity_id: UUID) -> Optional[AiExplainability]:
        return self.db.query(AiExplainability).filter(
            AiExplainability.tenant_id == tenant_id,
            AiExplainability.entity_type == entity_type,
            AiExplainability.entity_id == entity_id,
            AiExplainability.is_deleted == False
        ).order_by(AiExplainability.created_at.desc()).first()

    def list_explanations(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[AiExplainability]:
        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        query = self.db.query(AiExplainability).filter(
            AiExplainability.tenant_id == tenant_id,
            AiExplainability.is_deleted == False
        )

        if workspace_id:
            query = query.filter(AiExplainability.workspace_id == workspace_id)
        if project_id:
            query = query.filter(AiExplainability.project_id == project_id)
        if analysis_id:
            query = query.filter(AiExplainability.analysis_id == analysis_id)
        if entity_type:
            query = query.filter(AiExplainability.entity_type == entity_type)
        if entity_id:
            query = query.filter(AiExplainability.entity_id == entity_id)

        allowed_sort_fields = {"created_at", "entity_type"}
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        sort_col = getattr(AiExplainability, sort_by)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        return query.limit(limit).offset(offset).all()

    def count_explanations(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None
    ) -> int:
        query = self.db.query(AiExplainability).filter(
            AiExplainability.tenant_id == tenant_id,
            AiExplainability.is_deleted == False
        )

        if workspace_id:
            query = query.filter(AiExplainability.workspace_id == workspace_id)
        if project_id:
            query = query.filter(AiExplainability.project_id == project_id)
        if analysis_id:
            query = query.filter(AiExplainability.analysis_id == analysis_id)
        if entity_type:
            query = query.filter(AiExplainability.entity_type == entity_type)
        if entity_id:
            query = query.filter(AiExplainability.entity_id == entity_id)

        return query.count()
