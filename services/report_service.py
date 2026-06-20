from uuid import UUID
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.models import ProcessAnalysis, EsgScore, ScenarioSimulation
from app.services.sustainability_conformance_service import SustainabilityConformanceService
from app.services.carbon_fitness_service import CarbonFitnessService
from app.services.sustainability_digital_twin_service import SustainabilityDigitalTwinService
from app.services.ocel_service import OcelGenerationService

class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.conformance_service = SustainabilityConformanceService(db)
        self.carbon_fitness_service = CarbonFitnessService(db)
        self.digital_twin_service = SustainabilityDigitalTwinService(db)

    def _get_workspace_id(self, analysis_id: UUID) -> UUID:
        pa = self.db.query(ProcessAnalysis).filter(ProcessAnalysis.id == analysis_id).first()
        if not pa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
        return pa.workspace_id

    def generate_executive_report(self, analysis_id: UUID) -> Dict[str, Any]:
        workspace_id = self._get_workspace_id(analysis_id)
        
        conformance = self.conformance_service.get_latest(analysis_id) or {}
        carbon = self.carbon_fitness_service.get_latest(analysis_id) or {}
        twin = self.digital_twin_service.get_latest(analysis_id) or {}
        
        esg = self.db.query(EsgScore).filter(EsgScore.workspace_id == workspace_id).order_by(EsgScore.calculated_at.desc()).first()
        esg_score = esg.overall_score if esg else None # assuming it is stored as 0-100
        
        # Bug 1 fix: read event/case counts from OCEL snapshot (stored in ScenarioSimulation)
        ocel_svc = OcelGenerationService(self.db)
        ocel_latest = ocel_svc.get_latest(analysis_id) or {}
        total_events = ocel_latest.get("event_count") or None
        total_cases = ocel_latest.get("case_count") or None
        # Fallback: derive case count from conformance data if OCEL snapshot lacks it
        if total_cases is None:
            total_cases = conformance.get("case_count") or None

        kpis = {
            "total_events": total_events,
            "total_cases": total_cases,
            "esg_compliance_score": esg_score,
            "sustainability_conformance": conformance.get("sustainability_conformance"),
            "process_fitness": conformance.get("process_fitness"),
            "carbon_fitness": carbon.get("carbon_fitness"),
            "carbon_budget_utilization": carbon.get("budget_utilization_pct")
        }
        
        risks = conformance.get("deviations", [])
        hotspots = carbon.get("hotspots", [])
        
        recommendations = {
            "best_carbon_strategy": twin.get("best_carbon_strategy", {}),
            "best_esg_strategy": twin.get("best_esg_strategy", {}),
            "best_balanced_strategy": twin.get("best_balanced_strategy", {})
        }
        
        return {
            "executive_summary": {
                "report_type": "Executive Report",
                "analysis_id": str(analysis_id)
            },
            "kpis": kpis,
            "risks": risks,
            "hotspots": hotspots,
            "recommendations": recommendations
        }

    def generate_sustainability_conformance_report(self, analysis_id: UUID) -> Dict[str, Any]:
        workspace_id = self._get_workspace_id(analysis_id)
        conformance = self.conformance_service.get_latest(analysis_id) or {}
        
        return {
            "report_summary": {
                "report_type": "Sustainability Conformance Report",
                "analysis_id": str(analysis_id)
            },
            "conformance_data": conformance
        }

    def generate_carbon_intelligence_report(self, analysis_id: UUID) -> Dict[str, Any]:
        workspace_id = self._get_workspace_id(analysis_id)
        carbon = self.carbon_fitness_service.get_latest(analysis_id) or {}
        
        return {
            "report_summary": {
                "report_type": "Carbon Intelligence Report",
                "analysis_id": str(analysis_id)
            },
            "carbon_data": carbon
        }

    def generate_digital_twin_report(self, analysis_id: UUID) -> Dict[str, Any]:
        workspace_id = self._get_workspace_id(analysis_id)
        twin = self.digital_twin_service.get_latest(analysis_id) or {}
        
        return {
            "report_summary": {
                "report_type": "Digital Twin Report",
                "analysis_id": str(analysis_id)
            },
            "twin_data": twin
        }
