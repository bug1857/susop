from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import AiRecommendation

class AiRecommendationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, recommendation: AiRecommendation) -> AiRecommendation:
        self.db.add(recommendation)
        self.db.commit()
        self.db.refresh(recommendation)
        return recommendation

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[AiRecommendation]:
        return self.db.query(AiRecommendation).filter(
            AiRecommendation.id == id,
            AiRecommendation.tenant_id == tenant_id,
            AiRecommendation.is_deleted == False
        ).first()

    def list_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[AiRecommendation]:
        return self.db.query(AiRecommendation).filter(
            AiRecommendation.analysis_id == analysis_id,
            AiRecommendation.tenant_id == tenant_id,
            AiRecommendation.is_deleted == False
        ).all()

    def list_recommendations(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        recommendation_type: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[AiRecommendation]:
        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        query = self.db.query(AiRecommendation).filter(
            AiRecommendation.tenant_id == tenant_id,
            AiRecommendation.is_deleted == False
        )

        if workspace_id:
            query = query.filter(AiRecommendation.workspace_id == workspace_id)
        if project_id:
            query = query.filter(AiRecommendation.project_id == project_id)
        if analysis_id:
            query = query.filter(AiRecommendation.analysis_id == analysis_id)
        if recommendation_type:
            query = query.filter(AiRecommendation.recommendation_type == recommendation_type)
        if priority:
            query = query.filter(AiRecommendation.priority == priority)
        if status:
            query = query.filter(AiRecommendation.status == status)

        allowed_sort_by = {"created_at", "priority", "estimated_emission_reduction", "estimated_cost_reduction", "recommendation_type"}
        if sort_by not in allowed_sort_by:
            sort_by = "created_at"

        sort_col = getattr(AiRecommendation, sort_by)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        return query.limit(limit).offset(offset).all()

    def count_recommendations(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        recommendation_type: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        query = self.db.query(AiRecommendation).filter(
            AiRecommendation.tenant_id == tenant_id,
            AiRecommendation.is_deleted == False
        )

        if workspace_id:
            query = query.filter(AiRecommendation.workspace_id == workspace_id)
        if project_id:
            query = query.filter(AiRecommendation.project_id == project_id)
        if analysis_id:
            query = query.filter(AiRecommendation.analysis_id == analysis_id)
        if recommendation_type:
            query = query.filter(AiRecommendation.recommendation_type == recommendation_type)
        if priority:
            query = query.filter(AiRecommendation.priority == priority)
        if status:
            query = query.filter(AiRecommendation.status == status)

        return query.count()

    def latest_recommendation(self, project_id: UUID, tenant_id: UUID) -> Optional[AiRecommendation]:
        return self.db.query(AiRecommendation).filter(
            AiRecommendation.project_id == project_id,
            AiRecommendation.tenant_id == tenant_id,
            AiRecommendation.is_deleted == False
        ).order_by(AiRecommendation.created_at.desc()).first()

    def find_existing_recommendation(self, tenant_id: UUID, analysis_id: UUID, recommendation_type: str, title: str) -> Optional[AiRecommendation]:
        return self.db.query(AiRecommendation).filter(
            AiRecommendation.tenant_id == tenant_id,
            AiRecommendation.analysis_id == analysis_id,
            AiRecommendation.recommendation_type == recommendation_type,
            AiRecommendation.title == title,
            AiRecommendation.is_deleted == False
        ).first()
