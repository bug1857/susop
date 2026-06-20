from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
import uuid
from typing import Dict, Any, List

from app.core.database import get_db
from app.services.object_simulation_service import ObjectSimulationService

router = APIRouter(
    prefix="/object-simulation",
    tags=["Object-Centric Simulation"]
)

@router.post("/{analysis_id}/generate", response_model=Dict[str, Any])
def generate_object_simulation(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = ObjectSimulationService(db)
    try:
        return service.generate_and_persist(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate simulation: {str(e)}")

@router.get("/{analysis_id}", response_model=Dict[str, Any])
def get_object_simulation(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = ObjectSimulationService(db)
    try:
        return service.get_latest(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulation: {str(e)}")

@router.get("/{analysis_id}/best", response_model=Dict[str, Any])
def get_best_simulation(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = ObjectSimulationService(db)
    try:
        return service.get_best(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve best simulation: {str(e)}")

@router.get("/{analysis_id}/summary", response_model=Dict[str, Any])
def get_simulation_summary(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = ObjectSimulationService(db)
    try:
        return service.get_summary(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulation summary: {str(e)}")

@router.get("/{analysis_id}/history", response_model=List[Dict[str, Any]])
def get_simulation_history(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = ObjectSimulationService(db)
    try:
        return service.get_history(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulation history: {str(e)}")

@router.get("/{analysis_id}/version/{version}", response_model=Dict[str, Any])
def get_simulation_version(
    version: int = Path(...),
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = ObjectSimulationService(db)
    try:
        return service.get_version(analysis_id, version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulation version: {str(e)}")
