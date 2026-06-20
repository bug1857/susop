from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import ScenarioSimulation

class ScenarioSimulationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, simulation: ScenarioSimulation) -> ScenarioSimulation:
        self.db.add(simulation)
        self.db.commit()
        self.db.refresh(simulation)
        return simulation

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[ScenarioSimulation]:
        return self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.id == id,
            ScenarioSimulation.tenant_id == tenant_id,
            ScenarioSimulation.is_deleted == False
        ).first()

    def list_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[ScenarioSimulation]:
        return self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.tenant_id == tenant_id,
            ScenarioSimulation.is_deleted == False
        ).order_by(ScenarioSimulation.created_at.desc()).all()

    def list_simulations(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        scenario_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[ScenarioSimulation]:
        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        query = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.tenant_id == tenant_id,
            ScenarioSimulation.is_deleted == False
        )

        if workspace_id:
            query = query.filter(ScenarioSimulation.workspace_id == workspace_id)
        if project_id:
            query = query.filter(ScenarioSimulation.project_id == project_id)
        if analysis_id:
            query = query.filter(ScenarioSimulation.analysis_id == analysis_id)
        if scenario_type:
            query = query.filter(ScenarioSimulation.scenario_type == scenario_type)

        allowed_sort_by = {"created_at", "scenario_name", "reduction_percentage", "simulated_emissions"}
        if sort_by not in allowed_sort_by:
            sort_by = "created_at"

        sort_col = getattr(ScenarioSimulation, sort_by)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        return query.limit(limit).offset(offset).all()

    def count_simulations(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        scenario_type: Optional[str] = None
    ) -> int:
        query = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.tenant_id == tenant_id,
            ScenarioSimulation.is_deleted == False
        )

        if workspace_id:
            query = query.filter(ScenarioSimulation.workspace_id == workspace_id)
        if project_id:
            query = query.filter(ScenarioSimulation.project_id == project_id)
        if analysis_id:
            query = query.filter(ScenarioSimulation.analysis_id == analysis_id)
        if scenario_type:
            query = query.filter(ScenarioSimulation.scenario_type == scenario_type)

        return query.count()

    def latest_simulation(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None
    ) -> Optional[ScenarioSimulation]:
        query = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.tenant_id == tenant_id,
            ScenarioSimulation.is_deleted == False
        )

        if workspace_id:
            query = query.filter(ScenarioSimulation.workspace_id == workspace_id)
        if project_id:
            query = query.filter(ScenarioSimulation.project_id == project_id)
        if analysis_id:
            query = query.filter(ScenarioSimulation.analysis_id == analysis_id)

        return query.order_by(ScenarioSimulation.created_at.desc()).first()

    def get_latest_ocel_simulation(self, analysis_id: UUID) -> Optional[ScenarioSimulation]:
        """Compatibility wrapper used by OCEL interoperability service.
        Retrieves the latest OCEL simulation for the given analysis without requiring tenant scoping.
        """
        query = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.is_deleted == False,
        )
        return query.order_by(ScenarioSimulation.created_at.desc()).first()
