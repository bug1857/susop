from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.core.database import get_db
from app.services.object_carbon_service import ObjectCarbonAttributionService

router = APIRouter(
    prefix="/object-carbon",
    tags=["Object-Centric Carbon Attribution"]
)

@router.post("/{analysis_id}/generate", response_model=Dict[str, Any])
def generate_carbon_attribution(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Generates a new Object-Centric Carbon Attribution analysis.
    """
    try:
        service = ObjectCarbonAttributionService(db)
        return service.generate_and_persist(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}", response_model=Dict[str, Any])
def get_latest_carbon(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves the latest generated Object-Centric Carbon Attribution snapshot.
    """
    try:
        service = ObjectCarbonAttributionService(db)
        return service.get_latest(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/worst", response_model=Dict[str, Any])
def get_worst_object(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Returns the current worst-performing carbon object.
    """
    try:
        service = ObjectCarbonAttributionService(db)
        return service.get_worst_object(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/summary", response_model=Dict[str, Any])
def get_carbon_summary(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves the statistics summary of the latest snapshot.
    """
    try:
        service = ObjectCarbonAttributionService(db)
        return service.get_summary(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/objects", response_model=List[Dict[str, Any]])
def get_carbon_objects(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves individual object carbon footprint entries.
    """
    try:
        service = ObjectCarbonAttributionService(db)
        return service.get_objects(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/hotspots", response_model=List[Dict[str, Any]])
def get_carbon_hotspots(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves only carbon hotspots sorted deterministically.
    """
    try:
        service = ObjectCarbonAttributionService(db)
        return service.get_hotspots(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/history", response_model=List[Dict[str, Any]])
def get_carbon_history(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves snapshot history metadata only.
    """
    try:
        service = ObjectCarbonAttributionService(db)
        return service.get_history(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/version/{version}", response_model=Dict[str, Any])
def get_carbon_version(analysis_id: uuid.UUID, version: int, db: Session = Depends(get_db)):
    """
    Retrieves a specific version of the Object-Centric Carbon Attribution snapshot.
    """
    try:
        service = ObjectCarbonAttributionService(db)
        return service.get_version(analysis_id, version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
