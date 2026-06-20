from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.models import EsgScoringProfile, EsgScore, EsgKpiDefinition, EsgKpiValue
from app.repositories.esg_score_repository import EsgScoreRepository
from app.repositories.esg_profile_repository import EsgProfileRepository
from app.core.audit import log_activity

class EsgScoringService:
    def __init__(self, db: Session):
        self.db = db
        self.score_repo = EsgScoreRepository(db)
        self.profile_repo = EsgProfileRepository(db)

    def configure_scoring_profile(self, tenant_id: UUID, user_id: UUID, payload: dict) -> EsgScoringProfile:
        name = payload.get("name")
        env_w = payload.get("environmental_weight", 0.40)
        soc_w = payload.get("social_weight", 0.30)
        gov_w = payload.get("governance_weight", 0.30)
        kpi_weights = payload.get("kpi_weights", {})

        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile name is required")

        # Weights sum check: sum must be exactly 1.0 (or 100%)
        # Using a small epsilon comparison to bypass floating point inaccuracies
        if abs((env_w + soc_w + gov_w) - 1.0) > 1e-6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Category weights must sum to exactly 1.0 (got E={env_w}, S={soc_w}, G={gov_w})"
            )

        # Deactivate current active profile for this tenant
        active_profile = self.profile_repo.get_active_profile(tenant_id)
        if active_profile:
            active_profile.is_active = False

        new_profile = EsgScoringProfile(
            tenant_id=tenant_id,
            name=name,
            environmental_weight=env_w,
            social_weight=soc_w,
            governance_weight=gov_w,
            kpi_weights=kpi_weights,
            is_active=True,
            is_deleted=False
        )
        created = self.profile_repo.create(new_profile)
        log_activity(self.db, user_id, "kpi_updated", tenant_id, f"Scoring profile '{name}' activated")
        return created

    def calculate_esg_score(self, workspace_id: UUID, period: str, tenant_id: UUID, user_id: UUID) -> EsgScore:
        # Retrieve active scoring profile
        profile = self.profile_repo.get_active_profile(tenant_id)
        if not profile:
            # Seed standard default profile
            profile = EsgScoringProfile(
                tenant_id=tenant_id,
                name="Default Scoring Profile",
                environmental_weight=0.40,
                social_weight=0.30,
                governance_weight=0.30,
                kpi_weights={},
                is_active=True,
                is_deleted=False
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)

        # Retrieve active KPI definitions
        active_defs = self.db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_active == True,
            EsgKpiDefinition.is_deleted == False
        ).all()

        if not active_defs:
            # Return empty baseline ESG score if no KPIs defined
            score = EsgScore(
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                period=period,
                scoring_profile_id=profile.id,
                overall_score=0.0,
                environmental_score=0.0,
                social_score=0.0,
                governance_score=0.0,
                completeness_score=100.0,
                score_breakdown={},
                is_deleted=False,
                calculated_at=datetime.utcnow()
            )
            created = self.score_repo.create(score)
            log_activity(self.db, user_id, "esg_score_calculated", tenant_id, f"Calculated zero baseline score for period {period}")
            return created

        # Retrieve values for period
        values = self.db.query(EsgKpiValue).filter(
            EsgKpiValue.workspace_id == workspace_id,
            EsgKpiValue.period == period,
            EsgKpiValue.tenant_id == tenant_id,
            EsgKpiValue.is_deleted == False
        ).all()

        values_map = {val.kpi_definition_id: val.value for val in values}

        breakdown = {}
        env_weighted_sum = 0.0
        env_total_weight = 0.0
        soc_weighted_sum = 0.0
        soc_total_weight = 0.0
        gov_weighted_sum = 0.0
        gov_total_weight = 0.0

        total_kpi_count = len(active_defs)
        present_kpi_count = 0

        for kpi in active_defs:
            raw_value = values_map.get(kpi.id)
            kpi_weight = profile.kpi_weights.get(kpi.kpi_code, 1.0)

            if raw_value is not None:
                present_kpi_count += 1
                # Normalization logic
                normalized_score = 0.0
                calc_method = kpi.calculation_method or {}
                target = calc_method.get("target")
                direction = calc_method.get("direction", "maximize")

                if target is not None and target != 0.0:
                    if direction == "minimize":
                        if raw_value <= target:
                            normalized_score = 100.0
                        else:
                            normalized_score = max(0.0, 100.0 - ((raw_value - target) / target) * 100.0)
                    else:  # maximize
                        normalized_score = min(100.0, (raw_value / target) * 100.0)
                else:
                    normalized_score = min(100.0, max(0.0, raw_value))

                breakdown[kpi.kpi_code] = {
                    "raw_value": raw_value,
                    "normalized_score": normalized_score,
                    "weight": kpi_weight,
                    "status": "present"
                }
            else:
                normalized_score = 0.0
                breakdown[kpi.kpi_code] = {
                    "raw_value": None,
                    "normalized_score": 0.0,
                    "weight": kpi_weight,
                    "status": "missing"
                }

            # Accumulate category weighted sum
            if kpi.category == "Environmental":
                env_weighted_sum += normalized_score * kpi_weight
                env_total_weight += kpi_weight
            elif kpi.category == "Social":
                soc_weighted_sum += normalized_score * kpi_weight
                soc_total_weight += kpi_weight
            elif kpi.category == "Governance":
                gov_weighted_sum += normalized_score * kpi_weight
                gov_total_weight += kpi_weight

        # Calculate category averages
        env_score = (env_weighted_sum / env_total_weight) if env_total_weight > 0.0 else 0.0
        soc_score = (soc_weighted_sum / soc_total_weight) if soc_total_weight > 0.0 else 0.0
        gov_score = (gov_weighted_sum / gov_total_weight) if gov_total_weight > 0.0 else 0.0

        # Completeness Score
        completeness = (present_kpi_count / total_kpi_count) * 100.0

        # Overall Rollup Score
        overall_score = (
            (env_score * profile.environmental_weight) +
            (soc_score * profile.social_weight) +
            (gov_score * profile.governance_weight)
        )

        # Apply Completeness factor penalty
        overall_score = overall_score * (completeness / 100.0)

        # Build ESG score model using percentage values (0.0 to 100.0)
        new_score = EsgScore(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            period=period,
            scoring_profile_id=profile.id,
            overall_score=overall_score,
            environmental_score=env_score,
            social_score=soc_score,
            governance_score=gov_score,
            completeness_score=completeness,
            score_breakdown=breakdown,
            is_deleted=False,
            calculated_at=datetime.utcnow()
        )
        created = self.score_repo.create(new_score)
        log_activity(self.db, user_id, "esg_score_calculated", tenant_id, f"Calculated ESG Score for period {period}: {overall_score:.4f}")
        return created
