import os
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
import pm4py
import pandas as pd

from app.models.models import ProcessAnalysis, ProcessModel, Workspace
from app.repositories.process_analysis_repository import ProcessAnalysisRepository
from app.repositories.process_model_repository import ProcessModelRepository
from app.core.ocel_parser import parse_dataset_to_dataframe
from app.services.variant_service import VariantService
from app.services.bottleneck_service import BottleneckService
from app.services.process_graph_service import ProcessGraphService
from app.core.audit import log_activity

class ProcessDiscoveryService:
    def __init__(self, db: Session):
        self.db = db
        self.analysis_repo = ProcessAnalysisRepository(db)
        self.model_repo = ProcessModelRepository(db)
        self.variant_service = VariantService(db)
        self.bottleneck_service = BottleneckService(db)
        self.graph_service = ProcessGraphService(db)

    def trigger_discovery(
        self, 
        workspace_id: UUID, 
        project_id: UUID, 
        dataset_id: UUID, 
        tenant_id: UUID, 
        user_id: UUID,
        parent_analysis_id: UUID = None
    ) -> ProcessAnalysis:
        # Create start log
        workspace = self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        log_activity(self.db, user_id=user_id, action="process_analysis_started", tenant_id=tenant_id, details=f"Started discovery for dataset {dataset_id}")

        # Compute next version number
        existing = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.dataset_id == dataset_id,
            ProcessAnalysis.workspace_id == workspace_id,
            ProcessAnalysis.project_id == project_id,
            ProcessAnalysis.is_deleted == False
        ).all()
        version = len(existing) + 1
        
        # Determine parent analysis ID automatically if not supplied
        if not parent_analysis_id and len(existing) > 0:
            existing_sorted = sorted(existing, key=lambda x: x.analysis_version)
            parent_analysis_id = existing_sorted[-1].id

        # 1. Initialize process_analyses record
        new_analysis = ProcessAnalysis(
            id=uuid4(),
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_id=dataset_id,
            analysis_version=version,
            parent_analysis_id=parent_analysis_id,
            status="running",
            created_by=user_id,
            created_at=datetime.utcnow(),
            is_deleted=False
        )
        self.analysis_repo.create(new_analysis)

        try:
            # 2. Parse dataset
            df = parse_dataset_to_dataframe(dataset_id, tenant_id, workspace_id, self.db)

            # 3. Choose process miner algorithm
            unique_activities_count = df["concept:name"].nunique()
            miner_name = "Inductive Miner" if unique_activities_count < 20 else "Heuristics Miner"
            
            # PM4Py Discovery
            if miner_name == "Inductive Miner":
                pm4py.discover_process_tree_inductive(df)
            else:
                pm4py.discover_heuristics_net(df)

            # 4. Extract Start/End activities and frequencies
            start_activities = pm4py.get_start_activities(df)
            end_activities = pm4py.get_end_activities(df)
            
            # PM4Py DFG for transition frequencies
            dfg, start_acts, end_acts = pm4py.discover_dfg(df)
            
            # Activity frequencies
            activity_counts = df["concept:name"].value_counts().to_dict()
            
            # transition lists
            transitions = []
            for (source, target), freq in dfg.items():
                transitions.append({
                    "source": str(source),
                    "target": str(target),
                    "frequency": int(freq)
                })

            # Calculate throughput times
            case_durations = df.groupby("case:concept:name")["time:timestamp"].agg(["min", "max"])
            case_durations["duration_sec"] = (case_durations["max"] - case_durations["min"]).dt.total_seconds()
            avg_throughput = float(case_durations["duration_sec"].mean()) if not case_durations.empty else 0.0

            # Count unique objects / types
            obj_type_count = 0
            if "object_type" in df.columns:
                obj_type_count = int(df["object_type"].nunique())

            # Summary metrics metadata structure
            summary_metrics = {
                "total_events": int(len(df)),
                "total_cases": int(df["case:concept:name"].nunique()),
                "total_activities": int(unique_activities_count),
                "average_case_length": float(len(df) / df["case:concept:name"].nunique()) if len(df) > 0 else 0.0,
                "average_throughput_time": avg_throughput
            }

            model_meta = {
                "start_activities": {str(k): int(v) for k, v in start_activities.items()},
                "end_activities": {str(k): int(v) for k, v in end_activities.items()},
                "activity_frequencies": {str(k): int(v) for k, v in activity_counts.items()},
                "transition_frequencies": transitions,
                "summary_metrics": summary_metrics,
                "miner_selected": miner_name
            }

            # 5. Persist ProcessModel
            model_name = f"Discovered model for analysis {new_analysis.id}"
            pm = ProcessModel(
                id=uuid4(),
                analysis_id=new_analysis.id,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                project_id=project_id,
                model_name=model_name,
                activity_count=int(unique_activities_count),
                edge_count=len(dfg),
                node_count=int(unique_activities_count),
                object_type_count=obj_type_count,
                metadata_fields=model_meta,
                created_at=datetime.utcnow(),
                is_deleted=False
            )
            self.model_repo.create(pm)
            log_activity(self.db, user_id=user_id, action="process_model_created", tenant_id=tenant_id, details=f"Model: {model_name}")

            # 6. Extract and save variants
            self.variant_service.generate_and_save_variants(df, new_analysis.id, tenant_id, workspace_id, project_id)
            log_activity(self.db, user_id=user_id, action="variants_generated", tenant_id=tenant_id, details=f"Variants extracted for analysis: {new_analysis.id}")

            # 7. Extract and save bottlenecks
            self.bottleneck_service.generate_and_save_bottlenecks(df, new_analysis.id, tenant_id, workspace_id, project_id)
            log_activity(self.db, user_id=user_id, action="bottlenecks_generated", tenant_id=tenant_id, details=f"Bottlenecks extracted for analysis: {new_analysis.id}")

            # 8. Extract and save DFG graphs
            self.graph_service.generate_and_save_graphs(df, new_analysis.id, tenant_id, workspace_id, project_id)
            log_activity(self.db, user_id=user_id, action="graph_generated", tenant_id=tenant_id, details=f"Graph data saved for analysis: {new_analysis.id}")

            # 9. Update analysis success state
            new_analysis.status = "completed"
            new_analysis.completed_at = datetime.utcnow()
            self.analysis_repo.save(new_analysis)
            log_activity(self.db, user_id=user_id, action="process_analysis_completed", tenant_id=tenant_id, details=f"Analysis completed successfully (v{version})")

        except Exception as e:
            new_analysis.status = "failed"
            failure_reason = str(e)[:500]
            self.analysis_repo.save(new_analysis)
            
            log_activity(self.db, user_id=user_id, action="process_analysis_failed", tenant_id=tenant_id, details=f"Analysis failed: {failure_reason}")
            
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Process Mining failed: {str(e)}")

        return new_analysis
