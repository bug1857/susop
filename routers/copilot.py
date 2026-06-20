from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.models.models import User, UserRole, Workspace, Project, ProcessAnalysis, AiRecommendation
from app.schemas.schemas import (
    AiInsightListResponse,
    CarbonForecastListResponse,
    CarbonForecastCreate,
    CarbonForecastResponseEnvelope,
    ScenarioSimulationCreate,
    ScenarioSimulationResponse,
    ScenarioSimulationListResponse,
    AiRecommendationListResponse,
    RecommendationEvidenceListResponse,
    AiRecommendationCreate,
    AiExplainabilityCreate,
    AiExplainabilityListResponse,
    AiCopilotRequest,
    AiCopilotResponseSchema,
    AiCopilotListResponse
)
from app.services.ai_insight_service import AiInsightService
from app.services.carbon_forecast_service import CarbonForecastService
from app.services.scenario_simulation_service import ScenarioSimulationService
from app.services.ai_recommendation_service import AiRecommendationService
from app.services.explainability_service import ExplainabilityService
from app.services.ai_explainability_service import AiExplainabilityService
from app.services.ai_copilot_service import AiCopilotService


router = APIRouter(prefix="/copilot", tags=["copilot"])

def wrap_http_exception(he: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=he.status_code,
        content={
            "success": False,
            "data": None,
            "metadata": None,
            "errors": [{"code": "HTTP_ERROR", "message": he.detail}]
        }
    )

def wrap_unexpected_exception(e: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "metadata": None,
            "errors": [{"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred."}]
        }
    )

def get_tenant_context(
    user_id: UUID, 
    db: Session, 
    tenant_id: Optional[UUID] = None,
    workspace_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    analysis_id: Optional[UUID] = None,
    recommendation_id: Optional[UUID] = None
) -> UUID:
    if tenant_id:
        role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == tenant_id
        ).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
        return tenant_id

    # Infer organization context from target entities if user belongs to multiple organizations
    if recommendation_id:
        rec = db.query(AiRecommendation).filter(AiRecommendation.id == recommendation_id).first()
        if rec:
            role = db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.organization_id == rec.tenant_id
            ).first()
            if role:
                return rec.tenant_id

    if analysis_id:
        analysis = db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == analysis_id,
            ProcessAnalysis.is_deleted == False
        ).first()
        if analysis:
            role = db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.organization_id == analysis.tenant_id
            ).first()
            if role:
                return analysis.tenant_id

    if project_id:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if proj:
            ws = db.query(Workspace).filter(Workspace.id == proj.workspace_id).first()
            if ws:
                role = db.query(UserRole).filter(
                    UserRole.user_id == user_id,
                    UserRole.organization_id == ws.organization_id
                ).first()
                if role:
                    return ws.organization_id

    if workspace_id:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if ws:
            role = db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.organization_id == ws.organization_id
            ).first()
            if role:
                return ws.organization_id

    role = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User does not belong to any organization"
        )
    return role.organization_id

@router.get("/insights", response_model=AiInsightListResponse)
def get_insights(
    analysis_id: Optional[UUID] = Query(None),
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    tenant_id: Optional[UUID] = Query(None),
    severity: Optional[str] = Query(None),
    insight_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id, workspace_id=workspace_id, project_id=project_id, analysis_id=analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        service = AiInsightService(db)
        data = service.repo.list_active_insights(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            severity=severity,
            insight_type=insight_type,
            status=status,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        total = service.repo.count_active_insights(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            severity=severity,
            insight_type=insight_type,
            status=status
        )
            
        return {
            "success": True,
            "data": data,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/forecasts", response_model=CarbonForecastListResponse)
def get_forecasts(
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    analysis_id: Optional[UUID] = Query(None),
    tenant_id: Optional[UUID] = Query(None),
    forecast_method: Optional[str] = Query(None),
    forecast_period: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id, workspace_id=workspace_id, project_id=project_id, analysis_id=analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Enforce workspace validation
        if workspace_id:
            ws = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.organization_id == resolved_tenant_id
            ).first()
            if not ws:
                raise HTTPException(status_code=404, detail="Resource not found")

        # Enforce project validation
        if project_id:
            proj = db.query(Project).filter(
                Project.id == project_id,
                Project.workspace_id == workspace_id if workspace_id else Project.workspace_id
            ).first()
            if not proj:
                raise HTTPException(status_code=404, detail="Resource not found")

        # Enforce analysis validation
        if analysis_id:
            analysis = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == analysis_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.is_deleted == False
            ).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")

        service = CarbonForecastService(db)
        data = service.repo.list_forecasts(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            forecast_method=forecast_method,
            forecast_period=forecast_period,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        total = service.repo.count_forecasts(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            forecast_method=forecast_method,
            forecast_period=forecast_period
        )
            
        return {
            "success": True,
            "data": data,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.post("/forecasts/generate", response_model=CarbonForecastResponseEnvelope, status_code=status.HTTP_201_CREATED)
def generate_forecast(
    payload: CarbonForecastCreate,
    tenant_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id, workspace_id=payload.workspace_id, project_id=payload.project_id, analysis_id=payload.analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Validate workspace_id ownership
        ws = db.query(Workspace).filter(
            Workspace.id == payload.workspace_id,
            Workspace.organization_id == resolved_tenant_id
        ).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Resource not found")
            
        # Validate project_id ownership
        proj = db.query(Project).filter(
            Project.id == payload.project_id,
            Project.workspace_id == payload.workspace_id
        ).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Resource not found")
            
        # Validate analysis_id ownership
        if payload.analysis_id:
            analysis = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == payload.analysis_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.workspace_id == payload.workspace_id,
                ProcessAnalysis.project_id == payload.project_id,
                ProcessAnalysis.is_deleted == False
            ).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")

        # Exclusively delegate generation to service layer
        service = CarbonForecastService(db)
        forecast = service.generate_forecast(
            tenant_id=resolved_tenant_id,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            analysis_id=payload.analysis_id,
            forecast_period=payload.forecast_period,
            forecast_method=payload.forecast_method.value,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "data": forecast,
            "metadata": {},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.post("/simulations/run", response_model=ScenarioSimulationResponse, status_code=status.HTTP_201_CREATED)
def run_scenario_simulation(
    payload: ScenarioSimulationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Resolve tenant context strictly from user token/context
        resolved_tenant_id = get_tenant_context(current_user.id, db, None, workspace_id=payload.workspace_id, project_id=payload.project_id, analysis_id=payload.analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Validate workspace ownership
        ws = db.query(Workspace).filter(
            Workspace.id == payload.workspace_id,
            Workspace.organization_id == resolved_tenant_id
        ).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Resource not found")
            
        # Validate project ownership
        proj = db.query(Project).filter(
            Project.id == payload.project_id,
            Project.workspace_id == payload.workspace_id
        ).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Resource not found")
            
        # Validate analysis ownership (if provided)
        if payload.analysis_id:
            analysis = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == payload.analysis_id,
                ProcessAnalysis.project_id == payload.project_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.is_deleted == False
            ).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")
                
        service = ScenarioSimulationService(db)
        simulation = service.run_simulation(
            tenant_id=resolved_tenant_id,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            analysis_id=payload.analysis_id,
            scenario_name=payload.scenario_name,
            scenario_type=payload.scenario_type,
            baseline_reduction_percent=payload.baseline_reduction_percent,
            user_id=current_user.id,
            scenario_description=payload.scenario_description
        )
        
        return {
            "success": True,
            "data": simulation,
            "metadata": {},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/simulations", response_model=ScenarioSimulationListResponse)
def get_simulations(
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    analysis_id: Optional[UUID] = Query(None),
    scenario_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, None, workspace_id=workspace_id, project_id=project_id, analysis_id=analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Validate workspace ownership
        if workspace_id:
            ws = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.organization_id == resolved_tenant_id
            ).first()
            if not ws:
                raise HTTPException(status_code=404, detail="Resource not found")
                
        # Validate project ownership
        if project_id:
            proj = db.query(Project).filter(
                Project.id == project_id,
                Project.workspace_id == workspace_id if workspace_id else Project.workspace_id
            ).first()
            if not proj:
                raise HTTPException(status_code=404, detail="Resource not found")
                
        # Validate analysis ownership
        if analysis_id:
            analysis = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == analysis_id,
                ProcessAnalysis.project_id == project_id if project_id else ProcessAnalysis.project_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.is_deleted == False
            ).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")
                
        service = ScenarioSimulationService(db)
        data = service.repo.list_simulations(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            scenario_type=scenario_type,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total = service.repo.count_simulations(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            scenario_type=scenario_type
        )
            
        return {
            "success": True,
            "data": data,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.post("/recommendations/generate", response_model=AiRecommendationListResponse)
def generate_recommendations(
    payload: AiRecommendationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, None, workspace_id=payload.workspace_id, project_id=payload.project_id, analysis_id=payload.analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Validate workspace_id ownership
        ws = db.query(Workspace).filter(
            Workspace.id == payload.workspace_id,
            Workspace.organization_id == resolved_tenant_id
        ).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Resource not found")
            
        # Validate project_id ownership
        proj = db.query(Project).filter(
            Project.id == payload.project_id,
            Project.workspace_id == payload.workspace_id
        ).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Resource not found")
            
        # Validate analysis_id ownership
        if payload.analysis_id:
            analysis = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == payload.analysis_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.workspace_id == payload.workspace_id,
                ProcessAnalysis.project_id == payload.project_id,
                ProcessAnalysis.is_deleted == False
            ).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")

        service = AiRecommendationService(db)
        data = service.generate_recommendations(
            tenant_id=resolved_tenant_id,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            analysis_id=payload.analysis_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "data": data,
            "metadata": {"total": len(data)},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.get("/recommendations", response_model=AiRecommendationListResponse)
def get_recommendations(
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    analysis_id: Optional[UUID] = Query(None),
    recommendation_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, None, workspace_id=workspace_id, project_id=project_id, analysis_id=analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Security validation for provided context filters
        if workspace_id:
            ws = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.organization_id == resolved_tenant_id
            ).first()
            if not ws:
                raise HTTPException(status_code=404, detail="Resource not found")
        
        if project_id:
            proj_query = db.query(Project).filter(Project.id == project_id)
            if workspace_id:
                proj_query = proj_query.filter(Project.workspace_id == workspace_id)
            proj = proj_query.first()
            if not proj:
                raise HTTPException(status_code=404, detail="Resource not found")
                
        if analysis_id:
            analysis_query = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == analysis_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.is_deleted == False
            )
            if workspace_id:
                analysis_query = analysis_query.filter(ProcessAnalysis.workspace_id == workspace_id)
            if project_id:
                analysis_query = analysis_query.filter(ProcessAnalysis.project_id == project_id)
            analysis = analysis_query.first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")
        
        service = AiRecommendationService(db)
        data = service.list_recommendations(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            recommendation_type=recommendation_type,
            priority=priority,
            status=status,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total = service.count_recommendations(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            recommendation_type=recommendation_type,
            priority=priority,
            status=status
        )
        
        return {
            "success": True,
            "data": data,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/recommendations/{id}/evidence", response_model=RecommendationEvidenceListResponse)
def get_recommendation_evidence(
    id: UUID,
    tenant_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id, recommendation_id=id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        service = ExplainabilityService(db)
        data = service.retrieve_evidence(id, resolved_tenant_id)
        
        # Trigger lineage retrieval audit trace (prepare architecture)
        service.build_lineage(resolved_tenant_id, id, current_user.id)
        
        return {
            "success": True,
            "data": data,
            "metadata": {"total": len(data), "limit": 20, "offset": 0},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.post("/explanations/generate", response_model=AiExplainabilityListResponse)
def generate_explanation(
    payload: AiExplainabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, None, workspace_id=payload.workspace_id, project_id=payload.project_id, analysis_id=payload.analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Validate workspace_id ownership
        ws = db.query(Workspace).filter(
            Workspace.id == payload.workspace_id,
            Workspace.organization_id == resolved_tenant_id
        ).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Resource not found")
            
        # Validate project_id ownership
        proj = db.query(Project).filter(
            Project.id == payload.project_id,
            Project.workspace_id == payload.workspace_id
        ).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Resource not found")
            
        # Validate analysis_id ownership
        if payload.analysis_id:
            analysis = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == payload.analysis_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.workspace_id == payload.workspace_id,
                ProcessAnalysis.project_id == payload.project_id,
                ProcessAnalysis.is_deleted == False
            ).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")

        # Exclusively delegate generation to service layer
        service = AiExplainabilityService(db)
        explanation = service.generate_explanation(
            tenant_id=resolved_tenant_id,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            analysis_id=payload.analysis_id,
            entity_type=payload.entity_type.value,
            entity_id=payload.entity_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "data": [explanation],
            "metadata": {"total": 1},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.get("/explanations", response_model=AiExplainabilityListResponse)
def get_explanations(
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    analysis_id: Optional[UUID] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, None, workspace_id=workspace_id, project_id=project_id, analysis_id=analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Security validation for provided context filters
        if workspace_id:
            ws = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.organization_id == resolved_tenant_id
            ).first()
            if not ws:
                raise HTTPException(status_code=404, detail="Resource not found")
        
        if project_id:
            proj_query = db.query(Project).filter(Project.id == project_id)
            if workspace_id:
                proj_query = proj_query.filter(Project.workspace_id == workspace_id)
            proj = proj_query.first()
            if not proj:
                raise HTTPException(status_code=404, detail="Resource not found")
                
        if analysis_id:
            analysis_query = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == analysis_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.is_deleted == False
            )
            if workspace_id:
                analysis_query = analysis_query.filter(ProcessAnalysis.workspace_id == workspace_id)
            if project_id:
                analysis_query = analysis_query.filter(ProcessAnalysis.project_id == project_id)
            analysis = analysis_query.first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")
        
        service = AiExplainabilityService(db)
        data = service.list_explanations(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total = service.count_explanations(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        return {
            "success": True,
            "data": data,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.post("/generate", response_model=AiCopilotListResponse)
def generate_ai_response(
    payload: AiCopilotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, None, workspace_id=payload.workspace_id, project_id=payload.project_id, analysis_id=payload.analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Context security validation
        ws = db.query(Workspace).filter(
            Workspace.id == payload.workspace_id,
            Workspace.organization_id == resolved_tenant_id
        ).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        proj = db.query(Project).filter(
            Project.id == payload.project_id,
            Project.workspace_id == payload.workspace_id
        ).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Resource not found")

        if payload.analysis_id:
            analysis = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == payload.analysis_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.workspace_id == payload.workspace_id,
                ProcessAnalysis.project_id == payload.project_id,
                ProcessAnalysis.is_deleted == False
            ).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")

        service = AiCopilotService(db)
        response = service.generate_response(
            tenant_id=resolved_tenant_id,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            analysis_id=payload.analysis_id,
            entity_type=payload.entity_type.value,
            entity_id=payload.entity_id,
            request_type=payload.request_type.value,
            provider=payload.provider.value,
            user_id=current_user.id,
            user_query=payload.user_query
        )
        return {
            "success": True,
            "data": [response],
            "metadata": {"total": 1},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.get("/responses", response_model=AiCopilotListResponse)
def get_copilot_responses(
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    analysis_id: Optional[UUID] = Query(None),
    request_type: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, None, workspace_id=workspace_id, project_id=project_id, analysis_id=analysis_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        if workspace_id:
            ws = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.organization_id == resolved_tenant_id
            ).first()
            if not ws:
                raise HTTPException(status_code=404, detail="Resource not found")
        
        if project_id:
            proj = db.query(Project).filter(
                Project.id == project_id,
                Project.workspace_id == workspace_id
            ).first()
            if not proj:
                raise HTTPException(status_code=404, detail="Resource not found")

        if analysis_id:
            analysis = db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == analysis_id,
                ProcessAnalysis.tenant_id == resolved_tenant_id,
                ProcessAnalysis.workspace_id == workspace_id,
                ProcessAnalysis.project_id == project_id,
                ProcessAnalysis.is_deleted == False
            ).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Resource not found")
        
        service = AiCopilotService(db)
        data = service.list_responses(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            request_type=request_type,
            provider=provider,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        total = service.count_responses(
            tenant_id=resolved_tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            request_type=request_type,
            provider=provider
        )
        return {
            "success": True,
            "data": data,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.get("/health")
def get_copilot_health(
    workspace_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    import httpx
    from app.services.ai_copilot_service import OLLAMA_MODEL_NAME
    from app.models.models import SustainAiSettings
    
    target_model = OLLAMA_MODEL_NAME
    if workspace_id:
        settings = db.query(SustainAiSettings).filter(
            SustainAiSettings.workspace_id == workspace_id
        ).first()
        if settings and settings.model_name:
            target_model = settings.model_name
            
    url = "http://localhost:11434/api/tags"
    try:
        response = httpx.get(url, timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            if model_names:
                exists = any(
                    name == target_model or name == f"{target_model}:latest"
                    for name in model_names
                )
                if not exists:
                    active_model = model_names[0]
                else:
                    active_model = target_model
                return {
                    "provider": "OLLAMA",
                    "status": "healthy",
                    "model": active_model
                }
        
        return {
            "provider": "OLLAMA",
            "status": "unhealthy",
            "model": None
        }
    except Exception:
        return {
            "provider": "OLLAMA",
            "status": "unhealthy",
            "model": None
        }


