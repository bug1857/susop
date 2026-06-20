from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import RecommendationEvidence, AiRecommendation

class RecommendationEvidenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, evidence: RecommendationEvidence) -> RecommendationEvidence:
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def get_by_recommendation(self, recommendation_id: UUID, tenant_id: UUID) -> List[RecommendationEvidence]:
        return self.db.query(RecommendationEvidence).join(
            AiRecommendation, RecommendationEvidence.recommendation_id == AiRecommendation.id
        ).filter(
            RecommendationEvidence.recommendation_id == recommendation_id,
            AiRecommendation.tenant_id == tenant_id
        ).all()

    def find_existing_evidence(self, recommendation_id: UUID, entity_type: str, entity_id: UUID) -> Optional[RecommendationEvidence]:
        return self.db.query(RecommendationEvidence).filter(
            RecommendationEvidence.recommendation_id == recommendation_id,
            RecommendationEvidence.entity_type == entity_type,
            RecommendationEvidence.entity_id == entity_id
        ).first()
