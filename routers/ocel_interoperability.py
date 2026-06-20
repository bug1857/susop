"""
OCEL Interoperability Router – Phase 6
----------------------------------------
Provides REST endpoints for:
  - GET  /{analysis_id}/export         → full export wrapper
  - GET  /{analysis_id}/inspect        → OCEL statistics
  - POST /{analysis_id}/import         → import an export wrapper
  - GET  /{analysis_id}/import/history → list of import snapshots
  - POST /{analysis_id}/validate       → validate without persisting
"""
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ocel_interoperability_service import OcelInteroperabilityService

router = APIRouter(
    prefix="/ocel",
    tags=["OCEL Interoperability"],
)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@router.get("/{analysis_id}/export", response_model=Dict[str, Any])
def export_ocel(
    analysis_id: uuid.UUID,
    pm4py: bool = False,
    db: Session = Depends(get_db),
):
    """
    Return the full OCEL export wrapper for the latest generation snapshot.

    Add `?pm4py=true` to also run a live PM4Py roundtrip validation test.

    Response structure:
        {
          "metadata":            { analysis_id, ocel_version, snapshot_hash, ... },
          "simulation_metadata": { raw stored metadata },
          "pm4py_compatible":    true,
          "ocel":                { ocel:events (dict), ocel:objects (dict), ... },
          "pm4py_validation":    { ... }   ← only when pm4py=true
        }
    """
    try:
        svc = OcelInteroperabilityService(db)
        return svc.export_ocel_wrapper(analysis_id, run_pm4py_validation=pm4py)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Inspect
# ---------------------------------------------------------------------------

@router.get("/{analysis_id}/inspect", response_model=Dict[str, Any])
def inspect_ocel(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Return detailed statistics for the latest OCEL snapshot:
    object/event/relation counts, object types, lifecycle stats, orphan counts.
    """
    try:
        svc = OcelInteroperabilityService(db)
        return svc.inspect_ocel(analysis_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

@router.post("/{analysis_id}/import", response_model=Dict[str, Any])
def import_ocel(
    analysis_id: uuid.UUID,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Import and persist an OCEL export wrapper as a new immutable snapshot.

    Expects the full wrapper (as produced by /export):
        {
          "metadata":            { ... },
          "simulation_metadata": { ... },
          "pm4py_compatible":    true,
          "ocel":                { ocel:objects, ocel:events }
        }

    Returns a summary of the stored import snapshot.
    """
    try:
        svc = OcelInteroperabilityService(db)
        # user_context not available without auth here; pass empty dict
        # (tenant_id / workspace_id are resolved from the analysis record itself)
        return svc.import_ocel(payload, analysis_id, user_context={})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Import History
# ---------------------------------------------------------------------------

@router.get("/{analysis_id}/import/history", response_model=List[Dict[str, Any]])
def import_history(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Return all OCEL import snapshots for the given analysis, newest first.

    Each entry includes:
        id, import_version, ocel_version, snapshot_hash,
        snapshot_timestamp, pm4py_compatible, validation_summary
    """
    try:
        svc = OcelInteroperabilityService(db)
        return svc.get_import_history(analysis_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Validate (without persisting)
# ---------------------------------------------------------------------------

@router.post("/{analysis_id}/validate", response_model=Dict[str, Any])
def validate_ocel(
    analysis_id: uuid.UUID,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Validate an OCEL export wrapper without persisting it.

    Returns:
        { "valid": bool, "errors": [...], "warnings": [...], "statistics": {...} }
    """
    try:
        svc = OcelInteroperabilityService(db)
        return svc.validate_ocel(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# PM4Py Roundtrip Validation (Sprint 3D.1)
# ---------------------------------------------------------------------------

@router.get("/{analysis_id}/pm4py-validate", response_model=Dict[str, Any])
def pm4py_validate(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Run a live PM4Py ingest + write-back roundtrip test on the latest OCEL snapshot.

    This is the Sprint 3D.1 final audit gate:
      1. Export the latest OCEL body
      2. Write to temp file, ingest via pm4py.read_ocel_json()
      3. Write back via pm4py.write_ocel_json()
      4. Re-read and assert event/object counts are preserved

    Returns:
        {
          "passed": bool,
          "ingest_event_count": int,
          "ingest_object_count": int,
          "ingest_object_types": [...],
          "roundtrip_event_count": int,
          "roundtrip_object_count": int,
          "error": str | null
        }
    """
    try:
        svc = OcelInteroperabilityService(db)
        wrapper = svc.export_ocel_wrapper(analysis_id)
        ocel_body = wrapper.get("ocel", {})
        return svc.pm4py_roundtrip_validation(ocel_body)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

