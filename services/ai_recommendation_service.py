from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from fastapi import HTTPException

from app.models.models import (
    AiRecommendation,
    AiInsight,
    RecommendationPriority,
    RecommendationType,
    RecommendationEvidence
)
from app.repositories.ai_recommendation_repository import AiRecommendationRepository
from app.repositories.recommendation_evidence_repository import RecommendationEvidenceRepository
from app.core.audit import log_activity

RECOMMENDATION_METADATA_VERSION = 1

class AiRecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AiRecommendationRepository(db)
        self.evidence_repo = RecommendationEvidenceRepository(db)

    def generate_recommendations(
        self,
        tenant_id: UUID,
        workspace_id: UUID,
        project_id: UUID,
        analysis_id: Optional[UUID],
        user_id: UUID
    ) -> List[AiRecommendation]:
        # Query active, non-deleted insights
        query = self.db.query(AiInsight).filter(
            AiInsight.is_deleted == False
        )
        if analysis_id:
            query = query.filter(AiInsight.analysis_id == analysis_id)
        else:
            query = query.filter(AiInsight.project_id == project_id)
        insights = query.all()

        # Empty-Insight Protection
        if not insights:
            return []

        # Insight Ownership Validation
        for insight in insights:
            if (
                insight.tenant_id != tenant_id
                or insight.workspace_id != workspace_id
                or insight.project_id != project_id
            ):
                raise HTTPException(status_code=404, detail="Resource not found")

        recommendations = []
        for insight in insights:
            # Map insight to recommendation parameters
            insight_type = insight.insight_type
            severity = insight.severity

            # Determine recommendation type, title, and priority
            if insight_type == "carbon_hotspot":
                rec_type = RecommendationType.CARBON_HOTSPOT
                title = "Reduce emissions in hotspot process"
                rec_priority = (
                    RecommendationPriority.CRITICAL
                    if severity == "CRITICAL"
                    else RecommendationPriority.HIGH
                )
            elif insight_type == "process_bottleneck":
                rec_type = RecommendationType.PROCESS_BOTTLENECK
                title = "Optimize bottleneck process stage"
                rec_priority = (
                    RecommendationPriority.HIGH
                    if severity in ["CRITICAL", "HIGH"]
                    else RecommendationPriority.MEDIUM
                )
            elif insight_type == "conformance_risk":
                rec_type = RecommendationType.CONFORMANCE_RISK
                title = "Improve process compliance"
                rec_priority = RecommendationPriority.HIGH
            elif insight_type == "esg_risk":
                rec_type = RecommendationType.ESG_RISK
                title = "Improve ESG performance"
                rec_priority = RecommendationPriority.HIGH
            elif insight_type == "data_quality_risk":
                rec_type = RecommendationType.DATA_QUALITY
                title = "Improve sustainability data quality"
                rec_priority = RecommendationPriority.MEDIUM
            else:
                # If there are other unknown types, skip
                continue

            description = insight.description

            # Calculate estimated reductions based on priority
            if rec_priority == RecommendationPriority.CRITICAL:
                emission_reduction = 20.0
                cost_reduction = 10.0
            elif rec_priority == RecommendationPriority.HIGH:
                emission_reduction = 15.0
                cost_reduction = 7.0
            elif rec_priority == RecommendationPriority.MEDIUM:
                emission_reduction = 10.0
                cost_reduction = 5.0
            else:  # LOW
                emission_reduction = 5.0
                cost_reduction = 2.0

            # Confidence score clamping
            confidence_score = max(0.0, min(100.0, float(round(insight.confidence_score))))

            # Metadata versioning
            rec_metadata = {
                "recommendation_version": RECOMMENDATION_METADATA_VERSION,
                "source_insight_id": str(insight.id),
                "source_type": insight_type,
                "priority_rule": f"rule_{insight_type}",
                "confidence_score": round(insight.confidence_score)
            }

            # Deduplication
            existing = self.repo.find_existing_recommendation(
                tenant_id=tenant_id,
                analysis_id=analysis_id,
                recommendation_type=rec_type,
                title=title
            )

            if existing:
                rec = existing
            else:
                # Create and persist a new recommendation
                rec = AiRecommendation(
                    tenant_id=tenant_id,
                    workspace_id=workspace_id,
                    project_id=project_id,
                    analysis_id=analysis_id,
                    recommendation_type=rec_type,
                    title=title,
                    description=description,
                    estimated_emission_reduction=emission_reduction,
                    estimated_cost_reduction=cost_reduction,
                    priority=rec_priority,
                    status="ACTIVE",
                    recommendation_confidence_score=confidence_score,
                    recommendation_metadata=rec_metadata
                )
                rec = self.repo.create(rec)

                # Log activity audit event
                details_payload = {
                    "recommendation_id": str(rec.id),
                    "recommendation_type": rec_type,
                    "priority": rec_priority,
                    "source_insight_id": str(insight.id)
                }
                log_activity(
                    self.db,
                    user_id=user_id,
                    action="recommendation_generated",
                    tenant_id=tenant_id,
                    details=json.dumps(details_payload)
                )

            # Evidence Ownership Validation
            if (
                insight.tenant_id != tenant_id
                or insight.workspace_id != workspace_id
                or insight.project_id != project_id
            ):
                raise HTTPException(status_code=404, detail="Resource not found")

            # Check for existing evidence
            existing_evidence = self.evidence_repo.find_existing_evidence(
                recommendation_id=rec.id,
                entity_type="ai_insight",
                entity_id=insight.id
            )

            if not existing_evidence:
                evidence = RecommendationEvidence(
                    recommendation_id=rec.id,
                    entity_type="ai_insight",
                    entity_id=insight.id,
                    evidence_payload={"generated_from": "recommendation_engine"}
                )
                self.evidence_repo.create(evidence)

            recommendations.append(rec)

        return recommendations

    def retrieve_recommendations(self, analysis_id: UUID, tenant_id: UUID) -> List[AiRecommendation]:
        return self.repo.list_by_analysis(analysis_id, tenant_id)

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
        return self.repo.list_recommendations(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            recommendation_type=recommendation_type,
            priority=priority,
            status=status,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

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
        return self.repo.count_recommendations(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            recommendation_type=recommendation_type,
            priority=priority,
            status=status
        )
