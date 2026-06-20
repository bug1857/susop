from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.models.models import User, ProcessAnalysis
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/{analysis_id}")
def get_recommendations(
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

    engine = RecommendationEngine(db)
    return engine.get_latest_recommendations(analysis_id)

@router.get("/{analysis_id}/summary")
def get_recommendations_summary(
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

    engine = RecommendationEngine(db)
    recs = engine.get_latest_recommendations(analysis_id)

    critical_count = sum(1 for r in recs if r["severity"] == "Critical")
    high_count = sum(1 for r in recs if r["severity"] == "High")
    medium_count = sum(1 for r in recs if r["severity"] == "Medium")
    low_count = sum(1 for r in recs if r["severity"] == "Low")

    return {
        "total_recommendations": len(recs),
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count
    }

@router.get("/{analysis_id}/top")
def get_top_recommendation(
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

    engine = RecommendationEngine(db)
    recs = engine.get_latest_recommendations(analysis_id)
    if not recs:
        raise HTTPException(status_code=404, detail="No recommendations found for this analysis run.")
    
    # Return highest ranked recommendation only
    return recs[0]

@router.get("/{analysis_id}/categories")
def get_recommendations_by_categories(
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

    engine = RecommendationEngine(db)
    recs = engine.get_latest_recommendations(analysis_id)

    grouped = {}
    for r in recs:
        cat = r["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(r)
    return grouped

@router.get("/{analysis_id}/history")
def get_recommendations_history(
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

    engine = RecommendationEngine(db)
    return engine.get_history(analysis_id)

@router.get("/{analysis_id}/version/{version}")
def get_recommendations_by_version(
    analysis_id: UUID,
    version: int,
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

    engine = RecommendationEngine(db)
    try:
        return engine.get_version_recommendations(analysis_id, version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{analysis_id}/refresh", status_code=status.HTTP_201_CREATED)
def refresh_recommendations(
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

    RoleChecker(["Admin", "Manager", "Analyst"]).check_workspace_role(analysis.workspace_id, current_user.id, db)
    RoleChecker(["Admin", "Manager", "Analyst"]).check_project_role(analysis.project_id, current_user.id, db)

    engine = RecommendationEngine(db)
    recs = engine.generate_and_persist(analysis_id)

    # Log activity
    from app.core.audit import log_activity
    log_activity(
        db=db,
        user_id=current_user.id,
        action="recommendations_refreshed",
        tenant_id=analysis.tenant_id,
        details=f"Refreshed recommendations for analysis {analysis_id}. Recomputed version."
    )

    return recs
