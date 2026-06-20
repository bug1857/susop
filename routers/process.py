from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.ocel_parser import parse_dataset_to_dataframe
from app.models.models import (
    User, 
    Dataset, 
    Workspace, 
    Project,
    ProcessAnalysis, 
    ProcessModel, 
    ProcessVariant, 
    ProcessBottleneck, 
    ProcessGraph,
    UserRole
)
from app.schemas.schemas import (
    ProcessAnalysisCreate,
    ProcessAnalysisResponse,
    ProcessAnalysisSummaryResponse,
    ProcessVariantResponse,
    ProcessBottleneckResponse,
    ProcessGraphDataResponse,
    ConformanceCheckRequest,
    ConformanceResultResponse,
    ConformanceResultResponseEnvelope,
    ConformanceDeviationResponseEnvelope,
    ConformanceDeviationListResponseEnvelope,
    CarbonAttributionResponseEnvelope,
    EmissionHotspotListResponseEnvelope,
    CarbonFitnessResponseEnvelope
)
from app.services.process_discovery_service import ProcessDiscoveryService
from app.services.conformance_service import ConformanceService
from app.services.carbon_attribution_service import CarbonAttributionService

router = APIRouter(prefix="/process", tags=["process"])

def verify_analysis_access(
    analysis_id: UUID, 
    current_user: User, 
    db: Session, 
    required_roles: List[str] = None
) -> ProcessAnalysis:
    if required_roles is None:
        required_roles = ["Admin", "Manager", "Analyst", "Viewer"]
        
    analysis = db.query(ProcessAnalysis).filter(
        ProcessAnalysis.id == analysis_id,
        ProcessAnalysis.is_deleted == False
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Process analysis run not found")

    # Verify tenant isolation (prevent UUID probing)
    role_record = db.query(UserRole).filter(
        UserRole.user_id == current_user.id,
        UserRole.organization_id == analysis.tenant_id
    ).first()
    if not role_record:
        raise HTTPException(status_code=404, detail="Process analysis run not found")
        
    # Enforce isolation: workspace exist, project exist, tenant isolation
    workspace = db.query(Workspace).filter(Workspace.id == analysis.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Verify tenant access
    if analysis.tenant_id != workspace.organization_id:
        raise HTTPException(status_code=403, detail="Tenant access denied")
        
    # Verify project
    project = db.query(Project).filter(Project.id == analysis.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.workspace_id != analysis.workspace_id:
        raise HTTPException(status_code=400, detail="Project does not belong to the workspace")
        
    # Verify dataset
    dataset = db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
    if not dataset or dataset.is_deleted:
        raise HTTPException(status_code=404, detail="Dataset not found or has been deleted")
        
    if dataset.is_archived:
        raise HTTPException(status_code=400, detail="Associated dataset is archived")
        
    # Role validation
    RoleChecker(required_roles).check_workspace_role(analysis.workspace_id, current_user.id, db)
    RoleChecker(required_roles).check_project_role(analysis.project_id, current_user.id, db)
    
    # Check analysis archived status
    if analysis.archived_at is not None:
        raise HTTPException(status_code=400, detail="Cannot access an archived process analysis")
        
    return analysis

@router.post("/discover", response_model=ProcessAnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
def discover_process(
    payload: ProcessAnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce active workspace and project role checks (Requires Admin, Manager, or Analyst)
    RoleChecker(["Admin", "Manager", "Analyst"]).check_workspace_role(payload.workspace_id, current_user.id, db)
    RoleChecker(["Admin", "Manager", "Analyst"]).check_project_role(payload.project_id, current_user.id, db)
    
    # Verify workspace
    workspace = db.query(Workspace).filter(Workspace.id == payload.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Verify project belongs to workspace
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.workspace_id != payload.workspace_id:
        raise HTTPException(status_code=400, detail="Project does not belong to the workspace")
        
    # Verify dataset exists and is scoped correctly
    dataset = db.query(Dataset).filter(
        Dataset.id == payload.dataset_id,
        Dataset.workspace_id == payload.workspace_id,
        Dataset.is_deleted == False
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or has been deleted")
    if dataset.is_archived:
        raise HTTPException(status_code=400, detail="Cannot run process analysis on an archived dataset")
        
    # Verify parent analysis if provided
    if payload.parent_analysis_id:
        parent = db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == payload.parent_analysis_id,
            ProcessAnalysis.is_deleted == False
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent analysis not found")
        if parent.workspace_id != payload.workspace_id or parent.project_id != payload.project_id:
            raise HTTPException(status_code=400, detail="Parent analysis context mismatch")
            
    # Execute Process Discovery
    service = ProcessDiscoveryService(db)
    analysis = service.trigger_discovery(
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        dataset_id=payload.dataset_id,
        tenant_id=workspace.organization_id,
        user_id=current_user.id,
        parent_analysis_id=payload.parent_analysis_id
    )
    
    return analysis

@router.get("/history", response_model=List[ProcessAnalysisResponse])
def get_process_history(
    workspace_id: UUID,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify workspace role
    RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(workspace_id, current_user.id, db)
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    query = db.query(ProcessAnalysis).filter(
        ProcessAnalysis.workspace_id == workspace_id,
        ProcessAnalysis.is_deleted == False
    )
    
    if project_id:
        # Verify project role
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_project_role(project_id, current_user.id, db)
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.workspace_id != workspace_id:
            raise HTTPException(status_code=400, detail="Project does not belong to the workspace")
        query = query.filter(ProcessAnalysis.project_id == project_id)
        
    return query.order_by(ProcessAnalysis.created_at.desc()).all()

@router.get("/{id}", response_model=ProcessAnalysisSummaryResponse)
def get_process_analysis(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = verify_analysis_access(id, current_user, db)
    
    model = db.query(ProcessModel).filter(
        ProcessModel.analysis_id == id,
        ProcessModel.is_deleted == False
    ).first()
    
    # Calculate object centric summary dynamically from dataset
    object_centric_summary = {
        "object_types": [],
        "total_objects": 0,
        "event_object_relationships": 0,
        "object_interaction_count": 0
    }
    try:
        df = parse_dataset_to_dataframe(analysis.dataset_id, analysis.tenant_id, analysis.workspace_id, db)
        if "object_type" in df.columns:
            object_centric_summary["object_types"] = df["object_type"].dropna().unique().tolist()
        if "object_id" in df.columns:
            object_centric_summary["total_objects"] = int(df["object_id"].dropna().nunique())
        if "object_id" in df.columns and "object_type" in df.columns:
            object_centric_summary["event_object_relationships"] = int(df[["object_id", "object_type"]].notnull().all(axis=1).sum())
        if "object_id" in df.columns:
            object_centric_summary["object_interaction_count"] = int(df["object_id"].dropna().count())
    except Exception:
        pass
        
    summary_metrics = {}
    if model and model.metadata_fields:
        summary_metrics = dict(model.metadata_fields.get("summary_metrics", {}))
        
    summary_metrics["object_centric_summary"] = object_centric_summary
    
    return {
        "id": analysis.id,
        "tenant_id": analysis.tenant_id,
        "workspace_id": analysis.workspace_id,
        "project_id": analysis.project_id,
        "dataset_id": analysis.dataset_id,
        "analysis_version": analysis.analysis_version,
        "parent_analysis_id": analysis.parent_analysis_id,
        "status": analysis.status,
        "created_by": analysis.created_by,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at,
        "archived_at": analysis.archived_at,
        "summary_metrics": summary_metrics,
        "model_metadata": model.metadata_fields if model else None
    }

@router.get("/{id}/variants", response_model=List[ProcessVariantResponse])
def get_process_variants(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = verify_analysis_access(id, current_user, db)
    
    if analysis.status == "failed":
        raise HTTPException(status_code=400, detail="Cannot retrieve variants for a failed process analysis")
        
    variants = db.query(ProcessVariant).filter(
        ProcessVariant.analysis_id == id,
        ProcessVariant.is_deleted == False
    ).all()
    
    return variants

@router.get("/{id}/bottlenecks", response_model=List[ProcessBottleneckResponse])
def get_process_bottlenecks(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = verify_analysis_access(id, current_user, db)
    
    if analysis.status == "failed":
        raise HTTPException(status_code=400, detail="Cannot retrieve bottlenecks for a failed process analysis")
        
    bottlenecks = db.query(ProcessBottleneck).filter(
        ProcessBottleneck.analysis_id == id,
        ProcessBottleneck.is_deleted == False
    ).all()
    
    return bottlenecks

@router.get("/{id}/graph", response_model=ProcessGraphDataResponse)
def get_process_graphs(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = verify_analysis_access(id, current_user, db)
    
    if analysis.status == "failed":
        raise HTTPException(status_code=400, detail="Cannot retrieve graph for a failed process analysis")
        
    graph = db.query(ProcessGraph).filter(
        ProcessGraph.analysis_id == id,
        ProcessGraph.is_deleted == False
    ).first()
    
    if not graph:
        raise HTTPException(status_code=404, detail="Process graph not found")
        
    nodes = graph.graph_data.get("nodes", [])
    edges = graph.graph_data.get("edges", [])
    
    frequencies = {}
    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        freq = edge.get("frequency", 0)
        frequencies[f"{src}->{tgt}"] = freq
        
    metadata = {
        "node_count": graph.node_count,
        "edge_count": graph.edge_count,
        "graph_type": graph.graph_type
    }
    
    return {
        "nodes": nodes,
        "edges": edges,
        "frequencies": frequencies,
        "metadata": metadata
    }

from fastapi.responses import JSONResponse
from datetime import datetime

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

@router.post("/{id}/conformance", response_model=ConformanceResultResponseEnvelope, status_code=status.HTTP_201_CREATED)
def trigger_conformance_check(
    id: UUID,
    payload: ConformanceCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Enforce validation and isolation checks on the analysis ID
        analysis = verify_analysis_access(id, current_user, db, required_roles=["Admin", "Manager", "Analyst"])
        
        # Verify reference model existence and context
        from app.models.models import ReferenceModel
        ref_model = db.query(ReferenceModel).filter(
            ReferenceModel.id == payload.reference_model_id,
            ReferenceModel.tenant_id == analysis.tenant_id
        ).first()
        if not ref_model:
            raise HTTPException(status_code=404, detail="Reference model not found")
        if ref_model.workspace_id != analysis.workspace_id or ref_model.project_id != analysis.project_id:
            raise HTTPException(status_code=400, detail="Reference model context mismatch")
            
        conformance_service = ConformanceService(db)
        result = conformance_service.run_conformance_check(
            analysis_id=id,
            reference_model_id=payload.reference_model_id,
            tenant_id=analysis.tenant_id,
            workspace_id=analysis.workspace_id,
            project_id=analysis.project_id,
            user_id=current_user.id
        )
        return {
            "success": True,
            "data": result,
            "metadata": None,
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/{id}/conformance", response_model=ConformanceResultResponseEnvelope)
def get_conformance_checking(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        analysis = verify_analysis_access(id, current_user, db)
        conformance_service = ConformanceService(db)
        result = conformance_service.get_conformance_result(analysis.id, analysis.tenant_id)
        if not result:
            raise HTTPException(status_code=404, detail="Conformance result not found")
        return {
            "success": True,
            "data": result,
            "metadata": None,
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/{id}/deviations", response_model=ConformanceDeviationListResponseEnvelope)
def get_deviations(
    id: UUID,
    limit: int = Query(10, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort direction"),
    severity: Optional[str] = Query(None, description="Filter by deviation severity"),
    activity_name: Optional[str] = Query(None, description="Filter by activity name"),
    reference_model: Optional[UUID] = Query(None, description="Filter by reference model UUID"),
    analysis_version: Optional[int] = Query(None, description="Filter by analysis version"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        analysis = verify_analysis_access(id, current_user, db)
        
        from app.models.models import ConformanceDeviation, ConformanceResult
        query = db.query(ConformanceDeviation).filter(
            ConformanceDeviation.analysis_id == id,
            ConformanceDeviation.tenant_id == analysis.tenant_id
        )
        
        # Filtering
        if severity:
            query = query.filter(ConformanceDeviation.severity == severity)
        if activity_name:
            query = query.filter(ConformanceDeviation.activity_name == activity_name)
        if start_date:
            query = query.filter(ConformanceDeviation.created_at >= start_date)
        if end_date:
            query = query.filter(ConformanceDeviation.created_at <= end_date)
            
        if reference_model or analysis_version:
            query = query.join(ConformanceResult, ConformanceDeviation.result_id == ConformanceResult.id)
            if reference_model:
                query = query.filter(ConformanceResult.reference_model_id == reference_model)
            if analysis_version:
                query = query.filter(ConformanceResult.analysis_version == analysis_version)
                
        # Count total
        total_count = query.count()
        
        # Sorting
        if sort_by == "activity_name":
            sort_col = ConformanceDeviation.activity_name
        elif sort_by == "deviation_type":
            sort_col = ConformanceDeviation.deviation_type
        elif sort_by == "severity":
            sort_col = ConformanceDeviation.severity
        else:
            sort_col = ConformanceDeviation.created_at
            
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())
            
        deviations = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": deviations,
            "metadata": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/{id}/deviations/{deviation_id}", response_model=ConformanceDeviationResponseEnvelope)
def get_deviation_by_id(
    id: UUID,
    deviation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        analysis = verify_analysis_access(id, current_user, db)
        
        from app.models.models import ConformanceDeviation
        deviation = db.query(ConformanceDeviation).filter(
            ConformanceDeviation.id == deviation_id,
            ConformanceDeviation.analysis_id == id,
            ConformanceDeviation.tenant_id == analysis.tenant_id
        ).first()
        
        if not deviation:
            raise HTTPException(status_code=404, detail="Deviation not found")
            
        return {
            "success": True,
            "data": deviation,
            "metadata": None,
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/{id}/carbon-attribution", response_model=CarbonAttributionResponseEnvelope)
def get_carbon_attributions(
    id: UUID,
    recalculate: bool = Query(False, description="Force recalculation of carbon attribution"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        analysis = verify_analysis_access(id, current_user, db)

        # Verify conformance result exists
        from app.models.models import ConformanceResult, CarbonAttribution, ProcessVariant
        result = db.query(ConformanceResult).filter(
            ConformanceResult.analysis_id == id,
            ConformanceResult.tenant_id == analysis.tenant_id
        ).first()
        if not result:
            raise HTTPException(
                status_code=400,
                detail="Conformance check must be run first before executing carbon attribution calculations."
            )

        # ── Check if attributions already exist (cache-first) ──────────────────
        existing_attributions = db.query(CarbonAttribution).filter(
            CarbonAttribution.analysis_id == id,
            CarbonAttribution.tenant_id == analysis.tenant_id
        ).all()

        if existing_attributions and not recalculate:
            # Return cached data directly — no expensive recalculation
            variant_emissions = db.query(ProcessVariant).filter(
                ProcessVariant.analysis_id == id,
                ProcessVariant.tenant_id == analysis.tenant_id
            ).all()

            return {
                "success": True,
                "data": {
                    "activity_emissions": existing_attributions,
                    "variant_emissions": variant_emissions,
                    "carbon_budget": result.carbon_budget,
                    "actual_emissions": result.actual_emissions,
                    "excess_emissions": result.excess_emissions,
                    "carbon_fitness_score": result.carbon_fitness_score
                },
                "metadata": None,
                "errors": None
            }

        # ── Recalculate (first time or forced) ────────────────────────────────
        carbon_service = CarbonAttributionService(db)

        # Calculate carbon attribution (updates variant emissions, creates hotspots and attributions)
        calc_result = carbon_service.calculate_carbon_attribution(analysis.id, analysis.tenant_id)

        # Trigger AI Insight Generation so they are dynamically available in Copilot & Recommendations
        from app.services.ai_insight_service import AiInsightService
        insight_service = AiInsightService(db)
        try:
            insight_service.generate_insights(
                tenant_id=analysis.tenant_id,
                workspace_id=analysis.workspace_id,
                project_id=analysis.project_id,
                analysis_id=analysis.id,
                user_id=current_user.id
            )
        except Exception as exc:
            # Let it fail gracefully or log it so it does not block the main carbon response
            import logging
            logging.getLogger(__name__).warning(f"Failed to generate AI insights on carbon attribution calculation: {exc}")

        # Fetch updated activity emissions
        activity_emissions = db.query(CarbonAttribution).filter(
            CarbonAttribution.analysis_id == id,
            CarbonAttribution.tenant_id == analysis.tenant_id
        ).all()

        # Fetch variant emissions
        variant_emissions = db.query(ProcessVariant).filter(
            ProcessVariant.analysis_id == id,
            ProcessVariant.tenant_id == analysis.tenant_id
        ).all()

        # Reload updated ConformanceResult for accurate totals
        db.refresh(result)

        # Trigger Audit Log
        from app.core.audit import log_activity
        log_activity(
            db,
            user_id=current_user.id,
            action="carbon_attribution_completed",
            tenant_id=analysis.tenant_id,
            details=f"Calculated carbon attribution for Analysis {id}. Total emissions: {result.actual_emissions:.2f}"
        )

        return {
            "success": True,
            "data": {
                "activity_emissions": activity_emissions,
                "variant_emissions": variant_emissions,
                "carbon_budget": result.carbon_budget,
                "actual_emissions": result.actual_emissions,
                "excess_emissions": result.excess_emissions,
                "carbon_fitness_score": result.carbon_fitness_score
            },
            "metadata": None,
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.get("/{id}/hotspots", response_model=EmissionHotspotListResponseEnvelope)
def get_hotspots(
    id: UUID,
    limit: int = Query(10, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    sort_by: str = Query("emissions", description="Sort field"),
    sort_order: str = Query("desc", description="Sort direction"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    activity_name: Optional[str] = Query(None, description="Filter by activity name"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        analysis = verify_analysis_access(id, current_user, db)
        
        from app.models.models import EmissionHotspot
        query = db.query(EmissionHotspot).filter(
            EmissionHotspot.analysis_id == id,
            EmissionHotspot.tenant_id == analysis.tenant_id
        )
        
        # Filtering
        if severity:
            query = query.filter(EmissionHotspot.severity == severity)
        if activity_name:
            query = query.filter(EmissionHotspot.activity_name == activity_name)
        if start_date:
            query = query.filter(EmissionHotspot.created_at >= start_date)
        if end_date:
            query = query.filter(EmissionHotspot.created_at <= end_date)
            
        # Count total
        total_count = query.count()
        
        # Sorting column determination
        if sort_by == "activity_name":
            sort_col = EmissionHotspot.activity_name
        elif sort_by == "contribution_percentage":
            sort_col = EmissionHotspot.contribution_percentage
        elif sort_by == "severity":
            sort_col = EmissionHotspot.severity
        else:
            sort_col = EmissionHotspot.emissions
            
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())
            
        hotspots = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": hotspots,
            "metadata": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/{id}/carbon-fitness", response_model=CarbonFitnessResponseEnvelope)
def get_carbon_fitness(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        analysis = verify_analysis_access(id, current_user, db)
        
        from app.models.models import ConformanceResult
        result = db.query(ConformanceResult).filter(
            ConformanceResult.analysis_id == id,
            ConformanceResult.tenant_id == analysis.tenant_id
        ).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Conformance result (and carbon fitness) not found")
            
        compliance_factor = 1.0
        if result.carbon_budget > 0:
            compliance_factor = max(0.0, 1.0 - (result.excess_emissions / result.carbon_budget))
            
        return {
            "success": True,
            "data": {
                "carbon_fitness_score": result.carbon_fitness_score,
                "carbon_budget": result.carbon_budget,
                "actual_emissions": result.actual_emissions,
                "excess_emissions": result.excess_emissions,
                "budget_exceeded": result.budget_exceeded,
                "compliance_factor": compliance_factor,
                "formula": "Carbon Fitness = Structural Fitness * Budget Compliance Factor"
            },
            "metadata": None,
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

