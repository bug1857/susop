import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.green_rerouting_service import GreenReroutingService

router = APIRouter(
    prefix="/rerouting",
    tags=["Green Rerouting"]
)

@router.get("/{analysis_id}")
def get_latest_reroutes(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = GreenReroutingService(db)
    try:
        return service.get_latest(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{analysis_id}/top")
def get_top_reroute(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = GreenReroutingService(db)
    try:
        return service.get_top(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{analysis_id}/history")
def get_reroute_history(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = GreenReroutingService(db)
    try:
        return service.get_history(analysis_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{analysis_id}/version/{version}")
def get_specific_reroute_version(analysis_id: uuid.UUID, version: int, db: Session = Depends(get_db)):
    service = GreenReroutingService(db)
    try:
        return service.get_version(analysis_id, version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{analysis_id}/summary")
def get_rerouting_summary(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = GreenReroutingService(db)
    try:
        return service.get_summary(analysis_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{analysis_id}/generate")
def generate_new_rerouting_simulation(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    service = GreenReroutingService(db)
    try:
        return service.generate_and_persist(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
