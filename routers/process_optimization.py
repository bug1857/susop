import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.process_optimization_service import ProcessOptimizationService

router = APIRouter(
    prefix="/optimization",
    tags=["Process Optimization"]
)

@router.get("/{analysis_id}")
def get_latest_optimization_plans(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ProcessOptimizationService(db)
    try:
        return service.get_latest(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{analysis_id}/best")
def get_best_optimization_plan(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ProcessOptimizationService(db)
    try:
        return service.get_best(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{analysis_id}/history")
def get_optimization_history(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ProcessOptimizationService(db)
    try:
        return service.get_history(analysis_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{analysis_id}/version/{version}")
def get_specific_optimization_version(analysis_id: uuid.UUID, version: int, db: Session = Depends(get_db)):
    service = ProcessOptimizationService(db)
    try:
        return service.get_version(analysis_id, version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{analysis_id}/summary")
def get_optimization_summary(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ProcessOptimizationService(db)
    try:
        return service.get_summary(analysis_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{analysis_id}/generate")
def generate_new_optimization_plans(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ProcessOptimizationService(db)
    try:
        return service.generate_and_persist(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
