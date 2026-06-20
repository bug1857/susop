import os
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.models.models import User, ProcessAnalysis, ConformanceResult, CarbonAttribution
from app.services.brsr_service import BRSRService, REPORTS_DIR
from app.services.report_payload_service import ReportPayloadService, ReportPayloadValidationError

router = APIRouter(prefix="/brsr", tags=["brsr"])

PDF_DIR = os.path.join(REPORTS_DIR, "pdf")
DOCX_DIR = os.path.join(REPORTS_DIR, "docx")

class BRSRGenerateRequest(BaseModel):
    analysis_id: UUID

@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_brsr_report(
    payload: BRSRGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Verify eligibility
    analysis = db.query(ProcessAnalysis).filter(
        ProcessAnalysis.id == payload.analysis_id,
        ProcessAnalysis.is_deleted == False
    ).first()
    
    if not analysis or analysis.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Analysis is not eligible for BRSR generation."
        )

    conformance = db.query(ConformanceResult).filter(
        ConformanceResult.analysis_id == payload.analysis_id
    ).first()
    if not conformance:
        raise HTTPException(
            status_code=400,
            detail="Analysis is not eligible for BRSR generation."
        )

    carbon_exists = db.query(CarbonAttribution).filter(
        CarbonAttribution.analysis_id == payload.analysis_id
    ).first()
    if not carbon_exists:
        raise HTTPException(
            status_code=400,
            detail="Analysis is not eligible for BRSR generation."
        )

    # 2. Check roles
    RoleChecker(["Admin", "Manager", "Analyst"]).check_workspace_role(analysis.workspace_id, current_user.id, db)
    RoleChecker(["Admin", "Manager", "Analyst"]).check_project_role(analysis.project_id, current_user.id, db)

    # 3. Generate report
    service = BRSRService(db)
    try:
        report = service.generate_report(payload.analysis_id)
        
        # Trigger Audit Log
        from app.core.audit import log_activity
        log_activity(
            db=db,
            user_id=current_user.id,
            action="brsr_report_generated",
            tenant_id=analysis.tenant_id,
            details=f"Generated BRSR report version {report['report_version']} for analysis {analysis.id}. Workspace: {analysis.workspace_id}"
        )
        
        return {
            "report_id": report["report_id"],
            "generated_at": report["generated_at"],
            "status": report["status"],
            "report_version": report["report_version"],
            "report_completeness_score": report["report_completeness_score"],
            "audit_readiness": report["audit_readiness"]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )

@router.get("/history/{analysis_id}")
def get_brsr_history(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = db.query(ProcessAnalysis).filter(
        ProcessAnalysis.id == analysis_id,
        ProcessAnalysis.is_deleted == False
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(analysis.workspace_id, current_user.id, db)

    service = BRSRService(db)
    return service.list_versions_metadata(analysis_id)

@router.get("/latest/{analysis_id}")
def get_latest_brsr_report(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = db.query(ProcessAnalysis).filter(
        ProcessAnalysis.id == analysis_id,
        ProcessAnalysis.is_deleted == False
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(analysis.workspace_id, current_user.id, db)
    
    service = BRSRService(db)
    try:
        return service.get_latest_report(analysis_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No BRSR report generated for this analysis run yet.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/pdf")
def download_brsr_pdf(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate (or return cached) PDF export for a BRSR report."""
    service = BRSRService(db)
    try:
        report = service.get_report(report_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")

    # Access control
    workspace_id = UUID(report["workspace_id"])
    RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(workspace_id, current_user.id, db)

    # Export readiness validation
    try:
        normalized = ReportPayloadService.normalize_report(report)
        ReportPayloadService.validate_export_readiness(normalized)
    except ReportPayloadValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "Export readiness validation failed", "issues": exc.errors}
        )

    # Check for cached file first
    os.makedirs(PDF_DIR, exist_ok=True)
    pdf_path = os.path.join(PDF_DIR, f"brsr_{report_id}.pdf")

    if not os.path.exists(pdf_path):
        try:
            from app.services.pdf_export_service import PDFExportService
            PDFExportService.generate_pdf(normalized, pdf_path)

            # Update export metadata in the stored report
            report["pdf_available"] = True
            report["pdf_path"] = pdf_path
            report["last_exported_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            service.save_report_payload(report_id, report)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"BRSR_Report_v{report.get('report_version', 1)}_{report_id[:8]}.pdf"
    )

@router.get("/{report_id}/docx")
def download_brsr_docx(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate (or return cached) DOCX export for a BRSR report."""
    service = BRSRService(db)
    try:
        report = service.get_report(report_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")

    # Access control
    workspace_id = UUID(report["workspace_id"])
    RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(workspace_id, current_user.id, db)

    # Export readiness validation
    try:
        normalized = ReportPayloadService.normalize_report(report)
        ReportPayloadService.validate_export_readiness(normalized)
    except ReportPayloadValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "Export readiness validation failed", "issues": exc.errors}
        )

    # Check for cached file first
    os.makedirs(DOCX_DIR, exist_ok=True)
    docx_path = os.path.join(DOCX_DIR, f"brsr_{report_id}.docx")

    if not os.path.exists(docx_path):
        try:
            from app.services.docx_export_service import DocxExportService
            DocxExportService.generate_docx(normalized, docx_path)

            # Update export metadata in the stored report
            report["docx_available"] = True
            report["docx_path"] = docx_path
            report["last_exported_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            service.save_report_payload(report_id, report)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DOCX generation failed: {str(e)}")

    return FileResponse(
        path=docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"BRSR_Report_v{report.get('report_version', 1)}_{report_id[:8]}.docx"
    )

@router.get("/{report_id}")
def get_brsr_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = BRSRService(db)
    try:
        report = service.get_report(report_id)
        # Verify access to report's workspace
        workspace_id = UUID(report["workspace_id"])
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(workspace_id, current_user.id, db)
        return report
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
