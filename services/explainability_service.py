from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.models.models import RecommendationEvidence
from app.repositories.recommendation_evidence_repository import RecommendationEvidenceRepository
from app.core.audit import log_activity

class ExplainabilityService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RecommendationEvidenceRepository(db)

    def build_lineage(self, tenant_id: UUID, recommendation_id: UUID, user_id: UUID) -> List[RecommendationEvidence]:
        # Audit readiness placeholder logging
        log_activity(self.db, user_id, "lineage_retrieved", tenant_id, f"Built lineage placeholder for recommendation {recommendation_id}")
        return []

    def retrieve_evidence(self, recommendation_id: UUID, tenant_id: UUID) -> List[RecommendationEvidence]:
        return self.repo.get_by_recommendation(recommendation_id, tenant_id)
