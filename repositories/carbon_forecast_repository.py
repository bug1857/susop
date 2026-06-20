from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import CarbonForecast

class CarbonForecastRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, forecast: CarbonForecast) -> CarbonForecast:
        self.db.add(forecast)
        self.db.commit()
        self.db.refresh(forecast)
        return forecast

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[CarbonForecast]:
        return self.db.query(CarbonForecast).filter(
            CarbonForecast.id == id,
            CarbonForecast.tenant_id == tenant_id,
            CarbonForecast.is_deleted == False
        ).first()

    def list_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[CarbonForecast]:
        return self.db.query(CarbonForecast).filter(
            CarbonForecast.analysis_id == analysis_id,
            CarbonForecast.tenant_id == tenant_id,
            CarbonForecast.is_deleted == False
        ).order_by(CarbonForecast.created_at.desc()).all()

    def list_forecasts(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        forecast_method: Optional[str] = None,
        forecast_period: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[CarbonForecast]:
        # Capping limit at 100
        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        query = self.db.query(CarbonForecast).filter(
            CarbonForecast.tenant_id == tenant_id,
            CarbonForecast.is_deleted == False
        )
        if workspace_id:
            query = query.filter(CarbonForecast.workspace_id == workspace_id)
        if project_id:
            query = query.filter(CarbonForecast.project_id == project_id)
        if analysis_id:
            query = query.filter(CarbonForecast.analysis_id == analysis_id)
        if forecast_method:
            query = query.filter(CarbonForecast.forecast_method == forecast_method)
        if forecast_period:
            query = query.filter(CarbonForecast.forecast_period == forecast_period)

        # Sorting whitelist
        allowed_sort_fields = {"created_at", "forecast_period", "predicted_emissions", "forecast_method"}
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        sort_col = getattr(CarbonForecast, sort_by)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        return query.offset(offset).limit(limit).all()

    def count_forecasts(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        forecast_method: Optional[str] = None,
        forecast_period: Optional[str] = None
    ) -> int:
        query = self.db.query(CarbonForecast).filter(
            CarbonForecast.tenant_id == tenant_id,
            CarbonForecast.is_deleted == False
        )
        if workspace_id:
            query = query.filter(CarbonForecast.workspace_id == workspace_id)
        if project_id:
            query = query.filter(CarbonForecast.project_id == project_id)
        if analysis_id:
            query = query.filter(CarbonForecast.analysis_id == analysis_id)
        if forecast_method:
            query = query.filter(CarbonForecast.forecast_method == forecast_method)
        if forecast_period:
            query = query.filter(CarbonForecast.forecast_period == forecast_period)

        return query.count()

    def latest_forecast(
        self,
        tenant_id: UUID,
        workspace_id: UUID,
        project_id: UUID,
        analysis_id: Optional[UUID] = None
    ) -> Optional[CarbonForecast]:
        query = self.db.query(CarbonForecast).filter(
            CarbonForecast.tenant_id == tenant_id,
            CarbonForecast.workspace_id == workspace_id,
            CarbonForecast.project_id == project_id,
            CarbonForecast.is_deleted == False
        )
        if analysis_id:
            query = query.filter(CarbonForecast.analysis_id == analysis_id)
        return query.order_by(CarbonForecast.created_at.desc()).first()
