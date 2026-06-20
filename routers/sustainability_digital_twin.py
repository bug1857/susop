from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
import uuid
from typing import Dict, Any, List

from app.core.database import get_db
from app.services.sustainability_digital_twin_service import SustainabilityDigitalTwinService

router = APIRouter(
    prefix="/digital-twin",
    tags=["Sustainability Digital Twin Engine"]
)

@router.post("/{analysis_id}/simulate", response_model=Dict[str, Any])
def simulate_scenario(
    analysis_id: uuid.UUID = Path(...),
    scenario: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityDigitalTwinService(db)
    try:
        return service.generate_and_persist(analysis_id, scenario)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute digital twin simulation: {str(e)}")

@router.post("/{analysis_id}/optimize", response_model=Dict[str, Any])
def optimize_strategies_post(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityDigitalTwinService(db)
    try:
        return service.find_best_scenario(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find best strategies: {str(e)}")

@router.get("/{analysis_id}", response_model=Dict[str, Any])
def get_latest_simulation(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityDigitalTwinService(db)
    try:
        result = service.get_latest(analysis_id)
        if result is None:
            raise HTTPException(status_code=404, detail="No digital twin simulation found. Run a scenario simulation first.")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve latest simulation: {str(e)}")

@router.get("/{analysis_id}/version/{version}", response_model=Dict[str, Any])
def get_version_simulation(
    analysis_id: uuid.UUID = Path(...),
    version: int = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityDigitalTwinService(db)
    try:
        return service.get_version(analysis_id, version)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulation version: {str(e)}")

@router.get("/{analysis_id}/best", response_model=Dict[str, Any])
def get_best_strategies(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityDigitalTwinService(db)
    try:
        return service.find_best_scenario(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve best strategies: {str(e)}")

@router.get("/{analysis_id}/summary", response_model=Dict[str, Any])
def get_digital_twin_summary(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityDigitalTwinService(db)
    try:
        latest = service.get_latest(analysis_id)
        if latest is None:
            raise HTTPException(status_code=404, detail="No digital twin simulation found. Run a scenario simulation first.")
        proj_outputs = latest.get("projected_outputs", {})
        impact = latest.get("impact_analysis", {})
        return {
            "emissions_saved_kg": impact.get("emissions_saved_kg", 0.0),
            "esg_improvement": impact.get("esg_improvement", 0.0),
            "sustainability_conformance_change": impact.get("sustainability_conformance_change", 0.0),
            "risk_change": impact.get("risk_change", "UNCHANGED"),
            "projected_carbon_fitness": proj_outputs.get("projected_carbon_fitness", 0.0),
            "projected_esg_score": proj_outputs.get("projected_esg_score", 0.0),
            "confidence": latest.get("confidence", 0),
            "confidence_band": latest.get("confidence_band", "LOW"),
            "simulation_status": latest.get("simulation_status", "partial")
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulation summary: {str(e)}")

@router.get("/{analysis_id}/history", response_model=List[Dict[str, Any]])
def get_simulation_history(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityDigitalTwinService(db)
    try:
        return service.get_history(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulation history: {str(e)}")
