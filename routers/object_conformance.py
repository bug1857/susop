from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.core.database import get_db
from app.services.object_conformance_service import ObjectConformanceService

router = APIRouter(
    prefix="/object-conformance",
    tags=["Object-Centric Conformance"]
)

@router.post("/{analysis_id}/generate", response_model=Dict[str, Any])
def generate_conformance(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Generates a new Object-Centric Conformance analysis.
    """
    try:
        service = ObjectConformanceService(db)
        return service.generate_and_persist(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}", response_model=Dict[str, Any])
def get_latest_conformance(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves the latest generated Object-Centric Conformance snapshot.
    """
    try:
        service = ObjectConformanceService(db)
        return service.get_latest(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/worst", response_model=Dict[str, Any])
def get_worst_object(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Returns the current worst-performing object.
    """
    try:
        service = ObjectConformanceService(db)
        return service.get_worst_object(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/summary", response_model=Dict[str, Any])
def get_conformance_summary(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves the statistics summary of the latest snapshot.
    """
    try:
        service = ObjectConformanceService(db)
        return service.get_summary(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/objects", response_model=List[Dict[str, Any]])
def get_conformance_objects(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves individual object fitness entries.
    """
    try:
        service = ObjectConformanceService(db)
        return service.get_objects(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/deviations", response_model=List[Dict[str, Any]])
def get_conformance_deviations(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves all process deviation instances.
    """
    try:
        service = ObjectConformanceService(db)
        return service.get_deviations(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/history", response_model=List[Dict[str, Any]])
def get_conformance_history(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves snapshot history.
    """
    try:
        service = ObjectConformanceService(db)
        return service.get_history(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/version/{version}", response_model=Dict[str, Any])
def get_conformance_version(analysis_id: uuid.UUID, version: int, db: Session = Depends(get_db)):
    """
    Retrieves a specific version of the Object-Centric Conformance snapshot.
    """
    try:
        service = ObjectConformanceService(db)
        return service.get_version(analysis_id, version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
