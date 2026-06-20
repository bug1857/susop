from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import AiInsight

class AiInsightRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, insight: AiInsight) -> AiInsight:
        self.db.add(insight)
        self.db.commit()
        self.db.refresh(insight)
        return insight

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[AiInsight]:
        return self.db.query(AiInsight).filter(
            AiInsight.id == id,
            AiInsight.tenant_id == tenant_id,
            AiInsight.is_deleted == False
        ).first()

    def list_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[AiInsight]:
        return self.db.query(AiInsight).filter(
            AiInsight.analysis_id == analysis_id,
            AiInsight.tenant_id == tenant_id,
            AiInsight.is_deleted == False
        ).all()

    def find_existing_insight(
        self,
        tenant_id: UUID,
        analysis_id: UUID,
        insight_type: str,
        source_reference: str
    ) -> Optional[AiInsight]:
        return self.db.query(AiInsight).filter(
            AiInsight.tenant_id == tenant_id,
            AiInsight.analysis_id == analysis_id,
            AiInsight.insight_type == insight_type,
            AiInsight.source_reference == source_reference,
            AiInsight.is_deleted == False
        ).first()

    def list_active_insights(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        severity: Optional[str] = None,
        insight_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[AiInsight]:
        query = self.db.query(AiInsight).filter(
            AiInsight.tenant_id == tenant_id,
            AiInsight.is_deleted == False
        )
        if workspace_id:
            query = query.filter(AiInsight.workspace_id == workspace_id)
        if project_id:
            query = query.filter(AiInsight.project_id == project_id)
        if analysis_id:
            query = query.filter(AiInsight.analysis_id == analysis_id)
        if severity:
            query = query.filter(AiInsight.severity == severity)
        if insight_type:
            query = query.filter(AiInsight.insight_type == insight_type)
        if status:
            query = query.filter(AiInsight.status == status)

        # Sorting whitelist
        ALLOWED_SORT_FIELDS = {
            "created_at",
            "confidence_score",
            "severity",
            "insight_type",
            "status"
        }
        if sort_by not in ALLOWED_SORT_FIELDS:
            sort_by = "created_at"

        sort_col = getattr(AiInsight, sort_by, AiInsight.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        return query.offset(offset).limit(limit).all()

    def count_active_insights(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        severity: Optional[str] = None,
        insight_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        query = self.db.query(AiInsight).filter(
            AiInsight.tenant_id == tenant_id,
            AiInsight.is_deleted == False
        )
        if workspace_id:
            query = query.filter(AiInsight.workspace_id == workspace_id)
        if project_id:
            query = query.filter(AiInsight.project_id == project_id)
        if analysis_id:
            query = query.filter(AiInsight.analysis_id == analysis_id)
        if severity:
            query = query.filter(AiInsight.severity == severity)
        if insight_type:
            query = query.filter(AiInsight.insight_type == insight_type)
        if status:
            query = query.filter(AiInsight.status == status)
        return query.count()
