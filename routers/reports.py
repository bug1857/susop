from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, Optional
import os
import tempfile
import pandas as pd
from fastapi.responses import FileResponse
from app.services.pdf_export_service import PDFExportService

from app.core.database import get_db
from app.services.report_service import ReportService

router = APIRouter(
    prefix="/reports",
    tags=["Reporting Engine"]
)

def _handle_export(format: Optional[str], data: Dict[str, Any], prefix: str):
    if not format or format.lower() == "json":
        return data
    elif format.lower() == "pdf":
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        PDFExportService.generate_pdf(data, path)
        return FileResponse(path, filename=f"{prefix}_report.pdf", media_type="application/pdf")
    elif format.lower() in ["excel", "csv"]:
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        df = pd.json_normalize(data)
        df.to_csv(path, index=False)
        return FileResponse(path, filename=f"{prefix}_report.csv", media_type="text/csv")
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")

@router.get("/executive/{analysis_id}")
def get_executive_report(
    analysis_id: UUID = Path(...),
    format: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    try:
        data = service.generate_executive_report(analysis_id)
        return _handle_export(format, data, "executive")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate executive report: {str(e)}")

@router.get("/sustainability-conformance/{analysis_id}")
def get_sustainability_conformance_report(
    analysis_id: UUID = Path(...),
    format: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    try:
        data = service.generate_sustainability_conformance_report(analysis_id)
        return _handle_export(format, data, "sustainability_conformance")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate sustainability conformance report: {str(e)}")

@router.get("/carbon-intelligence/{analysis_id}")
def get_carbon_intelligence_report(
    analysis_id: UUID = Path(...),
    format: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    try:
        data = service.generate_carbon_intelligence_report(analysis_id)
        return _handle_export(format, data, "carbon_intelligence")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate carbon intelligence report: {str(e)}")

@router.get("/digital-twin/{analysis_id}")
def get_digital_twin_report(
    analysis_id: UUID = Path(...),
    format: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    try:
        data = service.generate_digital_twin_report(analysis_id)
        return _handle_export(format, data, "digital_twin")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate digital twin report: {str(e)}")
