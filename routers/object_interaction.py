from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.core.database import get_db
from app.services.object_interaction_service import ObjectInteractionService

router = APIRouter(
    prefix="/object-interactions",
    tags=["Object Interaction Analytics"]
)

@router.post("/{analysis_id}/generate", response_model=Dict[str, Any])
def generate_object_interactions(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        service = ObjectInteractionService(db)
        return service.generate_and_persist(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}", response_model=Dict[str, Any])
def get_latest_interactions(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        service = ObjectInteractionService(db)
        return service.get_latest(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/bottlenecks", response_model=List[Dict[str, Any]])
def get_bottlenecks(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        service = ObjectInteractionService(db)
        return service.get_bottlenecks(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/risk-paths", response_model=List[Dict[str, Any]])
def get_risk_paths(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        service = ObjectInteractionService(db)
        return service.get_risk_paths(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/summary", response_model=Dict[str, Any])
def get_interaction_summary(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        service = ObjectInteractionService(db)
        return service.get_summary(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/history", response_model=List[Dict[str, Any]])
def get_interaction_history(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        service = ObjectInteractionService(db)
        return service.get_history(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}/version/{version}", response_model=Dict[str, Any])
def get_interaction_version(analysis_id: uuid.UUID, version: int, db: Session = Depends(get_db)):
    try:
        service = ObjectInteractionService(db)
        return service.get_version(analysis_id, version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
