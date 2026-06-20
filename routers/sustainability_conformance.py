from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
import uuid
from typing import Dict, Any, List

from app.core.database import get_db
from app.services.sustainability_conformance_service import SustainabilityConformanceService

router = APIRouter(
    prefix="/sustainability-conformance",
    tags=["Sustainability Conformance Engine"]
)

@router.post("/{analysis_id}/calculate", response_model=Dict[str, Any])
def calculate_sustainability_conformance(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityConformanceService(db)
    try:
        return service.generate_and_persist(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate sustainability conformance: {str(e)}")

@router.get("/{analysis_id}", response_model=Dict[str, Any])
def get_latest_sustainability_conformance(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityConformanceService(db)
    try:
        result = service.get_latest(analysis_id)
        if result is None:
            raise HTTPException(status_code=404, detail="No sustainability conformance snapshot found. Click Calculate to generate one.")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sustainability conformance: {str(e)}")

@router.get("/{analysis_id}/version/{version}", response_model=Dict[str, Any])
def get_version_sustainability_conformance(
    analysis_id: uuid.UUID = Path(...),
    version: int = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityConformanceService(db)
    try:
        return service.get_version(analysis_id, version)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sustainability conformance version: {str(e)}")

@router.get("/{analysis_id}/deviations", response_model=List[Dict[str, Any]])
def get_sustainability_deviations(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityConformanceService(db)
    try:
        return service.detect_sustainability_deviations(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sustainability deviations: {str(e)}")

@router.get("/{analysis_id}/summary", response_model=Dict[str, Any])
def get_sustainability_conformance_summary(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityConformanceService(db)
    try:
        latest = service.get_latest(analysis_id)
        return {
            "process_fitness": latest.get("process_fitness", 0.0),
            "carbon_fitness": latest.get("carbon_fitness", 0.0),
            "sustainability_conformance": latest.get("sustainability_conformance", 0.0),
            "esg_compliance_score": latest.get("esg_compliance_score", 0.0),
            "sustainability_risk": latest.get("sustainability_risk", "LOW"),
            "deviation_count": len(latest.get("deviations", []))
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sustainability conformance summary: {str(e)}")

@router.get("/{analysis_id}/history", response_model=List[Dict[str, Any]])
def get_sustainability_conformance_history(
    analysis_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db)
):
    service = SustainabilityConformanceService(db)
    try:
        return service.get_history(analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sustainability conformance history: {str(e)}")
