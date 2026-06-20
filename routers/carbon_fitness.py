from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
import uuid
from typing import Dict, Any, List

from app.core.database import get_db
from app.services.carbon_fitness_service import CarbonFitnessService

router = APIRouter(
    prefix="/carbon-fitness",
    tags=["Carbon Fitness Engine"]
)

@router.post("/{analysis_id}/calculate", response_model=Dict[str, Any])
def calculate_carbon_fitness(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = CarbonFitnessService(db)
    try:
        return service.generate_and_persist(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate carbon fitness: {str(e)}")

@router.get("/{analysis_id}", response_model=Dict[str, Any])
def get_latest_carbon_fitness(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = CarbonFitnessService(db)
    try:
        return service.get_latest(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve carbon fitness: {str(e)}")

@router.get("/{analysis_id}/version/{version}", response_model=Dict[str, Any])
def get_version_carbon_fitness(
    analysis_id: uuid.UUID = Path(...),
    version: int = Path(...),
    db: Session = Depends(get_db)
):
    service = CarbonFitnessService(db)
    try:
        return service.get_version(analysis_id, version)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve carbon fitness version: {str(e)}")

@router.get("/{analysis_id}/violations", response_model=List[Dict[str, Any]])
def get_carbon_violations(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = CarbonFitnessService(db)
    try:
        return service.detect_green_violations(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve green violations: {str(e)}")

@router.get("/{analysis_id}/summary", response_model=Dict[str, Any])
def get_carbon_fitness_summary(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = CarbonFitnessService(db)
    try:
        latest = service.get_latest(analysis_id)
        violations = latest.get("violations", [])
        return {
            "process_fitness": latest.get("process_fitness", 0.0),
            "carbon_fitness": latest.get("carbon_fitness", 0.0),
            "sustainability_fitness": latest.get("sustainability_fitness", 0.0),
            "violation_count": len(violations)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve carbon fitness summary: {str(e)}")

@router.get("/{analysis_id}/history", response_model=List[Dict[str, Any]])
def get_carbon_fitness_history(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = CarbonFitnessService(db)
    try:
        return service.get_history(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve carbon fitness history: {str(e)}")
