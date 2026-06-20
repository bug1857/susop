from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.core.database import get_db
from app.services.ocel_service import OcelGenerationService

router = APIRouter(
    prefix="/ocel",
    tags=["OCEL 2.0 Generation"]
)

@router.post("/{analysis_id}/generate", response_model=Dict[str, Any])
def generate_ocel(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Generates a new OCEL 2.0 object-centric log snapshot.
    """
    try:
        service = OcelGenerationService(db)
        return service.generate_and_persist(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}", response_model=Dict[str, Any])
def get_latest_ocel(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves the latest generated OCEL 2.0 snapshot for the given analysis.
    """
    try:
        service = OcelGenerationService(db)
        return service.get_latest(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/version/{version}", response_model=Dict[str, Any])
def get_ocel_version(analysis_id: uuid.UUID, version: int, db: Session = Depends(get_db)):
    """
    Retrieves a specific version of the OCEL 2.0 snapshot.
    """
    try:
        service = OcelGenerationService(db)
        return service.get_version(analysis_id, version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/history", response_model=List[Dict[str, Any]])
def get_ocel_history(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves the generation history of OCEL snapshots for the given analysis.
    """
    try:
        service = OcelGenerationService(db)
        return service.get_history(analysis_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/summary", response_model=Dict[str, Any])
def get_ocel_summary(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves the statistics summary of the latest OCEL snapshot.
    """
    try:
        service = OcelGenerationService(db)
        return service.get_summary(analysis_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
