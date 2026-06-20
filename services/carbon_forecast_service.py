from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import func

from app.models.models import (
    CarbonForecast,
    ProcessAnalysis,
    ConformanceResult,
    CarbonAttribution,
    EsgKpiValue,
    EsgKpiDefinition,
    ForecastMethod
)
from app.repositories.carbon_forecast_repository import CarbonForecastRepository
from app.core.audit import log_activity

class CarbonForecastService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CarbonForecastRepository(db)

    def generate_forecast(
        self,
        tenant_id: UUID,
        workspace_id: UUID,
        project_id: UUID,
        analysis_id: Optional[UUID],
        forecast_period: str,
        forecast_method: str,
        user_id: UUID
    ) -> CarbonForecast:
        # 1. Forecast Method Validation
        if forecast_method not in [ForecastMethod.LINEAR_TREND, ForecastMethod.MOVING_AVERAGE]:
            raise HTTPException(
                status_code=400,
                detail="Invalid forecast method"
            )

        # 2. Historical Data Retrieval
        history = []

        # 2a. Fetch completed Process Analyses for this tenant, workspace, project
        analyses = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.tenant_id == tenant_id,
            ProcessAnalysis.workspace_id == workspace_id,
            ProcessAnalysis.project_id == project_id,
            ProcessAnalysis.status == "completed",
            ProcessAnalysis.is_deleted == False
        ).order_by(ProcessAnalysis.created_at.asc()).all()

        for analysis in analyses:
            # Check ConformanceResult first
            conf_res = self.db.query(ConformanceResult).filter(
                ConformanceResult.analysis_id == analysis.id
            ).first()
            if conf_res:
                history.append((analysis.created_at, conf_res.actual_emissions))
            else:
                # Fallback to Sum(CarbonAttribution.emissions)
                attr_sum = self.db.query(func.sum(CarbonAttribution.emissions)).filter(
                    CarbonAttribution.analysis_id == analysis.id
                ).scalar()
                if attr_sum is not None:
                    history.append((analysis.created_at, float(attr_sum)))

        # 2b. Enrich with Environmental ESG KPI values
        kpi_values = self.db.query(EsgKpiValue).join(EsgKpiDefinition).filter(
            EsgKpiValue.tenant_id == tenant_id,
            EsgKpiValue.workspace_id == workspace_id,
            EsgKpiValue.project_id == project_id,
            EsgKpiValue.is_deleted == False,
            EsgKpiDefinition.category == "Environmental",
            EsgKpiDefinition.is_deleted == False
        ).order_by(EsgKpiValue.calculated_at.asc()).all()

        for val in kpi_values:
            code = val.kpi_definition.kpi_code.upper()
            name = val.kpi_definition.name.upper()
            unit = val.kpi_definition.unit.upper()
            
            # Match environmental/carbon/emissions KPIs
            if any(term in code or term in name or term in unit for term in ["CO2", "EMISSION", "CARBON"]):
                history.append((val.calculated_at, val.value))

        # Sort chronologically
        history.sort(key=lambda x: x[0])
        emissions_series = [val for date, val in history]

        # 3. Minimum Historical Data check
        N = len(emissions_series)
        MIN_FORECAST_POINTS = 3
        if N < MIN_FORECAST_POINTS:
            raise HTTPException(
                status_code=400,
                detail="Insufficient historical data for forecasting"
            )

        # 4. Run Forecasting Algorithm
        if forecast_method == ForecastMethod.LINEAR_TREND:
            # Formula: d = (yN - y1) / (N - 1); forecast = yN + d
            d = (emissions_series[-1] - emissions_series[0]) / (N - 1)
            predicted = emissions_series[-1] + d
        else:  # MOVING_AVERAGE
            # Formula: forecast = average(last 3 observations)
            last_obs = emissions_series[-3:]
            predicted = sum(last_obs) / len(last_obs)

        # 5. Confidence Interval Calculation
        mean_obs = sum(emissions_series) / N
        variance_val = sum((y - mean_obs)**2 for y in emissions_series) / N
        std_dev = variance_val ** 0.5

        lower_bound = max(0.0, predicted - std_dev)
        upper_bound = predicted + std_dev

        # 6. Forecast Quality Score Calculation
        if mean_obs > 0.0:
            CV = std_dev / mean_obs
        else:
            CV = 0.0

        P_score = min(50.0, (N / 12.0) * 50.0)
        V_score = max(0.0, 50.0 * (1.0 - CV))
        confidence_score = max(0, min(100, round(P_score + V_score)))

        # 7. Metadata construction
        metadata = {
            "method": forecast_method,
            "historical_points": N,
            "variance": round(variance_val, 2),
            "forecast_horizon": forecast_period,
            "confidence_score": int(confidence_score)
        }

        # 8. Versioning and Persistence (New row, append-only)
        forecast = CarbonForecast(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            forecast_period=forecast_period,
            forecast_method=forecast_method,
            predicted_emissions=float(predicted),
            lower_bound=float(lower_bound),
            upper_bound=float(upper_bound),
            forecast_metadata=metadata,
            forecast_confidence_score=float(confidence_score),
            is_deleted=False
        )
        self.repo.create(forecast)

        # 9. Log Audit event
        log_activity(
            self.db,
            user_id,
            "forecast_generated",
            tenant_id,
            f"Generated carbon forecast for analysis {analysis_id}"
        )

        return forecast

    def retrieve_forecasts(self, analysis_id: UUID, tenant_id: UUID) -> List[CarbonForecast]:
        return self.repo.list_by_analysis(analysis_id, tenant_id)
