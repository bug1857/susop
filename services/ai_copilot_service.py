from uuid import UUID
from datetime import datetime
import time
import math
import hashlib
import json
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.models import (
    Workspace,
    Project,
    ProcessAnalysis,
    AiCopilotResponse,
    AiExplainability,
    AIProvider,
    AIRequestType,
    SustainAiSettings
)
from app.repositories.ai_copilot_repository import AiCopilotRepository
from app.repositories.ai_explainability_repository import AiExplainabilityRepository
from app.services.ai_explainability_service import AiExplainabilityService
from app.services.providers.provider_factory import ProviderFactory
from app.services.prompt_registry import PromptRegistry
from app.core.audit import log_activity

logger = logging.getLogger(__name__)

# Centralized constants
OLLAMA_MODEL_NAME = "qwen3:8b"
AI_PROMPT_VERSION = 1
MAX_AI_RESPONSE_TOKENS = 2000
MAX_AI_RESPONSE_CHARS = 8000
AI_PROVIDER_TIMEOUT_SECONDS = 120

class AiCopilotService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AiCopilotRepository(db)
        self.explainability_repo = AiExplainabilityRepository(db)
        self.explainability_service = AiExplainabilityService(db)

    def generate_response(
        self,
        tenant_id: UUID,
        workspace_id: UUID,
        project_id: UUID,
        analysis_id: Optional[UUID],
        entity_type: str,
        entity_id: UUID,
        request_type: str,
        provider: str,
        user_id: UUID,
        user_query: Optional[str] = None
    ) -> AiCopilotResponse:
        # 1. Ownership Validation
        workspace = self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace or workspace.organization_id != tenant_id:
            raise HTTPException(status_code=404, detail="Resource not found")

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project or project.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Resource not found")

        if analysis_id:
            analysis = self.db.query(ProcessAnalysis).filter(
                ProcessAnalysis.id == analysis_id,
                ProcessAnalysis.is_deleted == False
            ).first()
            if not analysis or analysis.tenant_id != tenant_id or analysis.workspace_id != workspace_id or analysis.project_id != project_id:
                raise HTTPException(status_code=404, detail="Resource not found")

        # 2. Cache Protection check (5 minute window) - Bypass if custom user_query is provided
        req_type_str = str(request_type).upper()
        if not user_query:
            existing_response = self.repository.latest_response(
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                project_id=project_id,
                entity_id=entity_id,
                request_type=req_type_str
            )
            if existing_response:
                time_diff = datetime.utcnow() - existing_response.created_at
                if time_diff.total_seconds() <= 300:
                    logger.info(f"Cache hit for entity {entity_id} request {request_type}. Returning cached response.")
                    return existing_response

        # 3. Explainability Dependency
        ent_type_str = str(entity_type).upper()
        explanation = self.explainability_repo.get_by_entity(tenant_id, ent_type_str, entity_id)
        if not explanation:
            try:
                explanation = self.explainability_service.generate_explanation(
                    tenant_id=tenant_id,
                    workspace_id=workspace_id,
                    project_id=project_id,
                    analysis_id=analysis_id,
                    entity_type=ent_type_str,
                    entity_id=entity_id,
                    user_id=user_id
                )
            except HTTPException as he:
                raise he
            except Exception as e:
                logger.warning(f"Failed to generate explainability record: {e}")
                explanation = None

        if not explanation:
            raise HTTPException(
                status_code=400,
                detail="Explainability record not found"
            )

        # 4. Prompt Construction
        # Sourced from workspace AI settings
        settings = self.db.query(SustainAiSettings).filter(
            SustainAiSettings.workspace_id == workspace_id
        ).first()

        selected_model = OLLAMA_MODEL_NAME
        quality_mode = "balanced"
        prompt_style = "sustainability_officer"
        response_style = "technical"

        if settings:
            selected_model = settings.model_name
            quality_mode = settings.quality_mode
            prompt_style = settings.prompt_style
            response_style = settings.response_style

        prompt = PromptRegistry.get_prompt(req_type_str, explanation.explanation_payload, quality_mode)

        # Inject BRSR report metadata and metrics context if generated
        import os
        latest_file = f"/Users/rudrapratapsingh/Desktop/newpro/backend/storage/reports/latest_brsr_{analysis_id}.json"
        if analysis_id and os.path.exists(latest_file):
            try:
                with open(latest_file, "r") as lf:
                    latest_data = json.load(lf)
                    report_id = latest_data.get("report_id")
                    report_path = f"/Users/rudrapratapsingh/Desktop/newpro/backend/storage/reports/brsr_{report_id}.json"
                    if os.path.exists(report_path):
                        with open(report_path, "r") as rf:
                            report_payload = json.load(rf)
                            brsr_context = f"\n\nActive BRSR Report Context:\n"
                            brsr_context += f"- Report ID: {report_payload.get('report_id')}\n"
                            brsr_context += f"- Report Version: {report_payload.get('report_version')}\n"
                            brsr_context += f"- Completeness Score: {report_payload.get('report_completeness_score')}%\n"
                            brsr_context += f"- Status: {report_payload.get('status')}\n"
                            brsr_context += f"- Section A General: {json.dumps(report_payload.get('section_a'))}\n"
                            brsr_context += f"- Section B Process Conformance: {json.dumps(report_payload.get('section_b'))}\n"
                            brsr_context += f"- Section C ESG & Performance: {json.dumps(report_payload.get('section_c'))}\n"
                            brsr_context += f"- Section D Traceability Matrix: {json.dumps(report_payload.get('section_d'))}\n"
                            prompt += brsr_context
            except Exception as e:
                logger.warning(f"Failed to inject BRSR context to copilot: {e}")

        # Inject Recommendations Context
        if analysis_id:
            try:
                from app.models.models import AiRecommendation
                from sqlalchemy import func
                max_ver = self.db.query(
                    func.max(func.json_extract(AiRecommendation.recommendation_metadata, '$.recommendation_version'))
                ).filter(
                    AiRecommendation.analysis_id == analysis_id,
                    AiRecommendation.is_deleted == False
                ).scalar()

                if max_ver is not None:
                    recs = self.db.query(AiRecommendation).filter(
                        AiRecommendation.analysis_id == analysis_id,
                        AiRecommendation.is_deleted == False,
                        func.json_extract(AiRecommendation.recommendation_metadata, '$.recommendation_version') == max_ver
                    ).all()

                    # Sort by priority score
                    def get_priority_score(r):
                        meta = r.recommendation_metadata or {}
                        return meta.get("priority_score", 0)
                    recs_sorted = sorted(recs, key=get_priority_score, reverse=True)

                    if recs_sorted:
                        critical_count = sum(1 for r in recs_sorted if r.priority.upper() == "CRITICAL")
                        total_carbon_savings = sum(r.estimated_emission_reduction for r in recs_sorted)

                        cat_counts = {}
                        for r in recs_sorted:
                            meta = r.recommendation_metadata or {}
                            cat = meta.get("category", r.recommendation_type)
                            cat_counts[cat] = cat_counts.get(cat, 0) + 1

                        rec_context = f"\n\nActive AI Recommendations Context (Latest Run):\n"
                        rec_context += f"- Critical Recommendations: {critical_count}\n"
                        rec_context += f"- Potential Carbon Savings: {total_carbon_savings:.1f} kg\n"
                        rec_context += f"- Category Distribution: {json.dumps(cat_counts)}\n"
                        rec_context += f"- Top Recommendation: {recs_sorted[0].title} (Priority Score: {recs_sorted[0].recommendation_metadata.get('priority_score', 0)}, Severity: {recs_sorted[0].priority.capitalize()})\n"
                        
                        rec_context += "\nRanked Recommendations:\n"
                        for i, r in enumerate(recs_sorted, 1):
                            meta = r.recommendation_metadata or {}
                            rec_context += f"Rank #{i} Opportunity:\n"
                            rec_context += f"  - ID: {r.id}\n"
                            rec_context += f"  - Title: {r.title}\n"
                            rec_context += f"  - Category: {meta.get('category', r.recommendation_type)}\n"
                            rec_context += f"  - Severity: {r.priority.capitalize()}\n"
                            rec_context += f"  - Priority Score: {meta.get('priority_score', 0)}\n"
                            rec_context += f"  - Confidence: {r.recommendation_confidence_score}%\n"
                            rec_context += f"  - Estimated Carbon Reduction: {r.estimated_emission_reduction} kg\n"
                            rec_context += f"  - Estimated Cost Savings: ${r.estimated_cost_reduction}\n"
                            rec_context += f"  - Estimated Compliance Improvement: {meta.get('estimated_compliance_improvement', 0.0)}%\n"
                            rec_context += f"  - Evidence: {json.dumps(meta.get('evidence', []))}\n"
                            rec_context += f"  - Source: Engine: {meta.get('source_engine')}, Table: {meta.get('source_table')}, Rule: {meta.get('generated_rule')}\n"
                        
                        prompt += rec_context
            except Exception as e:
                logger.warning(f"Failed to inject recommendations context to copilot: {e}")

        # Inject Green Rerouting Context
        if analysis_id and req_type_str == "SIMULATION_EXPLANATION":
            try:
                from app.services.green_rerouting_service import GreenReroutingService
                grs = GreenReroutingService(self.db)
                latest_reroutes = grs.get_latest(analysis_id)
                summary = grs.get_summary(analysis_id)
                if latest_reroutes:
                    top_reroute = latest_reroutes[0]
                    route_context = f"\n\nActive Green Rerouting Context:\n"
                    route_context += f"- Total Reroutes: {summary.get('total_reroutes')}\n"
                    route_context += f"- Total Carbon Savings: {summary.get('total_carbon_savings')} kg\n"
                    route_context += f"- Best Reroute Activity: {top_reroute.get('candidate_activity')} -> {top_reroute.get('candidate_action')}\n"
                    route_context += f"- Best Reroute Savings: {top_reroute.get('projected_savings')} kg CO2e\n"
                    route_context += f"- Best Reroute Projected Fitness: {top_reroute.get('projected_fitness')}\n"
                    route_context += f"- Best Reroute Confidence: {top_reroute.get('confidence_score')}\n"
                    prompt += route_context
            except Exception as e:
                logger.warning(f"Failed to inject green rerouting context to copilot: {e}")

        # Inject Process Optimization Context
        if analysis_id and req_type_str == "SIMULATION_EXPLANATION":
            try:
                from app.services.process_optimization_service import ProcessOptimizationService
                pos = ProcessOptimizationService(self.db)
                latest_opt = pos.get_latest(analysis_id)
                opt_summary = pos.get_summary(analysis_id)
                if latest_opt:
                    best_opt = latest_opt[0]
                    opt_context = f"\n\nActive Process Optimization Context:\n"
                    opt_context += f"- Total Strategies: {opt_summary.get('total_strategies')}\n"
                    opt_context += f"- Total Carbon Savings: {opt_summary.get('total_carbon_savings')} kg\n"
                    opt_context += f"- Best Strategy Name: {best_opt.get('strategy_name')}\n"
                    opt_context += f"- Best Strategy Score: {best_opt.get('strategy_score')}\n"
                    opt_context += f"- Best Strategy Carbon Savings: {best_opt.get('total_carbon_savings_kg')} kg\n"
                    opt_context += f"- Best Strategy Projected Fitness: {best_opt.get('projected_final_fitness')}\n"
                    opt_context += f"- Best Strategy Confidence: {best_opt.get('optimization_confidence')}\n"
                    opt_context += f"- Best Strategy Hops: {len(best_opt.get('hops', []))}\n"
                    prompt += opt_context
            except Exception as e:
                logger.warning(f"Failed to inject process optimization context to copilot: {e}")

        # Inject Object Conformance Context
        if analysis_id:
            try:
                from app.services.object_conformance_service import ObjectConformanceService
                ocs = ObjectConformanceService(self.db)
                latest_conf = ocs.get_latest(analysis_id)
                worst_obj = ocs.get_worst_object(analysis_id)
                summary = ocs.get_summary(analysis_id)
                
                conf_context = f"\n\nActive Object Conformance Context:\n"
                conf_context += f"- Total Objects: {summary.get('object_count')}\n"
                conf_context += f"- Average Fitness: {summary.get('average_fitness')}\n"
                conf_context += f"- Critical Objects: {summary.get('critical_objects')}\n"
                conf_context += f"- High Risk Objects: {summary.get('high_objects')}\n"
                conf_context += f"- Worst Performing Object Type: {summary.get('worst_object_type', {}).get('object_type')}\n"
                if worst_obj:
                    conf_context += f"- Worst Object: {worst_obj.get('object_id')} (Type: {worst_obj.get('object_type')}, Fitness: {worst_obj.get('fitness_score')}, Severity: {worst_obj.get('severity')}, Deviations: {worst_obj.get('deviation_count')})\n"
                conf_context += f"- Object Type Summary: {json.dumps(summary.get('object_type_summary'))}\n"
                
                # Top deviations
                deviations = ocs.get_deviations(analysis_id)
                if deviations:
                    top_devs = deviations[:5]
                    conf_context += f"- Top Deviations: {json.dumps(top_devs)}\n"
                
                prompt += conf_context
            except Exception as e:
                logger.warning(f"Failed to inject object conformance context to copilot: {e}")

        # Inject Object Carbon Context
        if analysis_id:
            try:
                from app.services.object_carbon_service import ObjectCarbonAttributionService
                ocas = ObjectCarbonAttributionService(self.db)
                summary = ocas.get_summary(analysis_id)
                worst_obj = ocas.get_worst_object(analysis_id)
                
                carbon_context = f"\n\nActive Object Carbon Context:\n"
                carbon_context += f"- Total Object Emissions: {summary.get('total_object_emissions')} kg\n"
                carbon_context += f"- Critical Carbon Objects: {summary.get('critical_objects')}\n"
                carbon_context += f"- High Carbon Objects: {summary.get('high_objects')}\n"
                carbon_context += f"- Worst Carbon Performing Object Type: {summary.get('worst_object_type', {}).get('object_type')}\n"
                if worst_obj:
                    carbon_context += f"- Worst Carbon Object: {worst_obj.get('object_id')} (Type: {worst_obj.get('object_type')}, Emissions: {worst_obj.get('emissions')} kg, Severity: {worst_obj.get('severity')})\n"
                carbon_context += f"- Object Type Carbon Summary: {json.dumps(summary.get('object_type_summary'))}\n"
                
                # Top hotspots
                hotspots = ocas.get_hotspots(analysis_id)
                if hotspots:
                    carbon_context += f"- Top Carbon Hotspots: {json.dumps(hotspots[:5])}\n"
                
                prompt += carbon_context
            except Exception as e:
                logger.warning(f"Failed to inject object carbon context to copilot: {e}")

        # Inject Object Interaction Context
        if analysis_id:
            try:
                from app.services.object_interaction_service import ObjectInteractionService
                ois = ObjectInteractionService(self.db)
                summary = ois.get_summary(analysis_id)
                bottlenecks = ois.get_bottlenecks(analysis_id)
                risk_paths = ois.get_risk_paths(analysis_id)
                
                interaction_context = f"\n\nActive Object Interaction Context:\n"
                interaction_context += f"- Total Relationships: {summary.get('total_relationships')}\n"
                interaction_context += f"- Bottleneck Count: {summary.get('bottleneck_count')}\n"
                interaction_context += f"- High Risk Objects: {summary.get('high_risk_objects')}\n"
                
                highest_risk = summary.get("highest_risk_object", {})
                if highest_risk:
                    interaction_context += f"- Highest Risk Object: {highest_risk.get('object_id')} (Risk Score: {highest_risk.get('risk_score')})\n"
                
                highest_carbon_path = summary.get("highest_carbon_path", {})
                if highest_carbon_path:
                    interaction_context += f"- Highest Carbon Path: {' -> '.join(highest_carbon_path.get('path', []))} ({highest_carbon_path.get('total_emissions_kg')} kg)\n"
                
                if bottlenecks:
                    top_b = bottlenecks[0]
                    interaction_context += f"- Top Bottleneck: {top_b.get('object_id')} (Score: {top_b.get('bottleneck_score')})\n"
                
                prompt += interaction_context
            except Exception as e:
                logger.warning(f"Failed to inject object interaction context to copilot: {e}")

        # Inject Object Simulation Context
        if analysis_id:
            try:
                from app.services.object_simulation_service import ObjectSimulationService
                oss = ObjectSimulationService(self.db)
                best_sim = oss.get_best(analysis_id)
                if best_sim:
                    sim_context = f"\n\nActive Object Simulation Context:\n"
                    sim_context += f"- Best Strategy: {best_sim.get('strategy')}\n"
                    sim_context += f"- Impact Score: {best_sim.get('impact_score')}\n"
                    sim_context += f"- Confidence: {best_sim.get('confidence')}\n"
                    sim_context += f"- Projected Carbon Change: {best_sim.get('projected_carbon_change_kg')} kg\n"
                    sim_context += f"- Projected Fitness Change: {best_sim.get('projected_fitness_change')}\n"
                    sim_context += f"- Projected Risk Change: {best_sim.get('projected_risk_change')}\n"
                    prompt += sim_context
            except Exception as e:
                logger.warning(f"Failed to inject object simulation context to copilot: {e}")

        # Inject Carbon Fitness Context
        if analysis_id:
            try:
                from app.services.carbon_fitness_service import CarbonFitnessService
                cfs = CarbonFitnessService(self.db)
                latest_fit = cfs.get_latest(analysis_id)
                if latest_fit:
                    fit_context = f"\n\nActive Carbon Fitness & Sustainability Context:\n"
                    fit_context += f"- Process Fitness: {latest_fit.get('process_fitness')}\n"
                    fit_context += f"- Carbon Fitness: {latest_fit.get('carbon_fitness')}\n"
                    fit_context += f"- Sustainability Fitness: {latest_fit.get('sustainability_fitness')}\n"
                    fit_context += f"- Carbon Budget: {latest_fit.get('carbon_budget_kg')} kg\n"
                    fit_context += f"- Actual Emissions: {latest_fit.get('actual_emissions_kg')} kg\n"
                    fit_context += f"- Budget Utilization: {latest_fit.get('budget_utilization_pct')}%\n"
                    
                    violations = latest_fit.get("violations", [])
                    fit_context += f"- Active Violations Count: {len(violations)}\n"
                    for v in violations[:3]:
                        fit_context += f"  * Violation: {v.get('violation_type')} | Severity: {v.get('severity')} | Carbon Impact: {v.get('carbon_impact_kg')} kg | Action: {v.get('recommended_action')}\n"
                        
                    recs = latest_fit.get("recommendations", [])
                    if recs:
                        fit_context += f"- Projected Carbon Reduction: {recs[0].get('expected_carbon_reduction_kg')} kg (via Top Recommendation: {recs[0].get('title')} with confidence {recs[0].get('confidence')}%)\n"
                    prompt += fit_context
            except Exception as e:
                logger.warning(f"Failed to inject carbon fitness context to copilot: {e}")

        # Inject Sustainability Conformance Context
        if analysis_id:
            try:
                from app.services.sustainability_conformance_service import SustainabilityConformanceService
                scs = SustainabilityConformanceService(self.db)
                latest_sc = scs.get_latest(analysis_id)
                if latest_sc:
                    sc_context = f"\n\nActive Sustainability Conformance Context:\n"
                    sc_context += f"- Sustainability Conformance Score: {latest_sc.get('sustainability_conformance')}\n"
                    sc_context += f"- ESG Compliance Score: {latest_sc.get('esg_compliance_score')}\n"
                    sc_context += f"- Sustainability Risk Level: {latest_sc.get('sustainability_risk')}\n"
                    
                    deviations = latest_sc.get("deviations", [])
                    sc_context += f"- Sustainability Deviations Count: {len(deviations)}\n"
                    for dev in deviations[:3]:
                        sc_context += f"  * Deviation: {dev.get('type')} | Severity: {dev.get('severity')} | Impact Score: {dev.get('impact_score')} | Recommended Action: {dev.get('recommended_action')}\n"
                    prompt += sc_context
            except Exception as e:
                logger.warning(f"Failed to inject sustainability conformance context to copilot: {e}")

        # Inject Sustainability Digital Twin Context
        if analysis_id:
            try:
                from app.services.sustainability_digital_twin_service import SustainabilityDigitalTwinService
                dt_service = SustainabilityDigitalTwinService(self.db)
                
                # Fetch latest digital twin snapshot
                latest_dt = dt_service.get_latest(analysis_id)
                if latest_dt:
                    dt_context = f"\n\nActive Sustainability Digital Twin State & Projections:\n"
                    dt_context += f"- Active Simulated Scenario: {latest_dt.get('scenario_name')}\n"
                    dt_context += f"- Baseline Version: v{latest_dt.get('baseline_version')} -> Projected Version: v{latest_dt.get('digital_twin_version')}\n"
                    dt_context += f"- Simulation Status: {latest_dt.get('simulation_status')}\n"
                    dt_context += f"- Simulation Confidence: {latest_dt.get('confidence')}% (Band: {latest_dt.get('confidence_band')})\n"
                    
                    proj = latest_dt.get("projected_outputs", {})
                    dt_context += f"- Projected Conformance Score: {proj.get('projected_sustainability_conformance')}\n"
                    dt_context += f"- Projected ESG Score: {proj.get('projected_esg_score')}\n"
                    dt_context += f"- Projected Emissions: {proj.get('projected_emissions_kg')} kg CO2e\n"
                    dt_context += f"- Projected Risk Level: {proj.get('projected_risk_level')}\n"
                    
                    impact = latest_dt.get("impact_analysis", {})
                    dt_context += f"- Projected Emissions Saved: {impact.get('emissions_saved_kg')} kg ({impact.get('emissions_saved_pct')}%)\n"
                    dt_context += f"- Projected ESG Improvement: +{impact.get('esg_improvement')} points\n"
                    
                    # Also inject optimization strategies
                    best_sc = dt_service.find_best_scenario(analysis_id)
                    best_carbon = best_sc.get("best_carbon_strategy", {})
                    best_balanced = best_sc.get("best_balanced_strategy", {})
                    
                    dt_context += f"- Optimal Strategy Recommendations:\n"
                    dt_context += f"  * Best Carbon Reduction Strategy: {best_carbon.get('scenario_name')} (Projected Emissions Saved: {best_carbon.get('impact_analysis', {}).get('emissions_saved_kg')} kg)\n"
                    dt_context += f"  * Best Balanced Strategy: {best_balanced.get('scenario_name')} (Projected Conformance Improvement: +{best_balanced.get('impact_analysis', {}).get('sustainability_conformance_change')} points)\n"
                    
                    prompt += dt_context
            except Exception as e:
                logger.warning(f"Failed to inject sustainability digital twin context to copilot: {e}")

        if user_query:
            prompt = f"User Question: {user_query}\n\nContext:\n{prompt}"

        # 5. Prompt Hash (SHA-256)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        
        # Logging protection: log hash only, never raw prompt
        logger.info(f"Prompt hash generated: {prompt_hash}")

        # 6. AI Generation with timings and auto-repair gate
        logger.info(f"Ollama provider using model: {selected_model}")
        ai_provider = ProviderFactory.get_provider(selected_model)
        
        import re
        start_time = time.monotonic()

        # Grounded Intent Router
        is_grounded_query = False
        grounded_response = None
        
        if user_query and analysis_id:
            uq_clean = user_query.strip().lower()
            
            # 5. Emissions Lineage
            if "explain how total emissions" in uq_clean or "emissions lineage" in uq_clean or "emissions were calculated" in uq_clean:
                try:
                    import pandas as pd
                    from app.core.ocel_parser import parse_dataset_to_dataframe
                    from app.models.models import Dataset
                    
                    analysis = self.db.query(ProcessAnalysis).filter(ProcessAnalysis.id == analysis_id).first()
                    dataset = self.db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
                    df = parse_dataset_to_dataframe(analysis.dataset_id, analysis.tenant_id, analysis.workspace_id, self.db)
                    
                    mappings = dataset.mappings or {}
                    def get_col_by_role(role_name):
                        for col, role in mappings.items():
                            if role == role_name:
                                return col
                        return None
                        
                    shipment_id_col = get_col_by_role("shipment_id") or "shipment_id"
                    carbon_col = "carbon_emissions" if "carbon_emissions" in df.columns else (get_col_by_role("carbon_emissions") or "emissions_kg")
                    
                    df[carbon_col] = pd.to_numeric(df[carbon_col], errors="coerce").fillna(0.0)
                    shipment_totals = df.groupby(shipment_id_col)[carbon_col].sum().to_dict()
                    total_val = sum(shipment_totals.values())
                    
                    lines = []
                    for sh_id, val in sorted(shipment_totals.items()):
                        lines.append(f"{sh_id} = {int(val)} kg")
                    lines.append(f"Total = {int(total_val)} kg")
                    
                    grounded_response = "\n".join(lines)
                    is_grounded_query = True
                except Exception as e:
                    logger.warning(f"Failed to calculate emissions lineage dynamically: {e}")

            # 1. Total Emissions
            elif "total emissions" in uq_clean:
                from app.services.object_carbon_service import ObjectCarbonAttributionService
                try:
                    ocas = ObjectCarbonAttributionService(self.db)
                    total_emissions = ocas.get_summary(analysis_id).get("total_object_emissions", 0.0)
                    grounded_response = f"{int(total_emissions)} kg"
                    is_grounded_query = True
                except Exception as e:
                    logger.warning(f"Failed to calculate total emissions dynamically: {e}")

            # 2. Supplier Emissions
            elif "supplier" in uq_clean and "emission" in uq_clean:
                try:
                    import pandas as pd
                    from app.core.ocel_parser import parse_dataset_to_dataframe
                    from app.models.models import Dataset
                    
                    analysis = self.db.query(ProcessAnalysis).filter(ProcessAnalysis.id == analysis_id).first()
                    dataset = self.db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
                    df = parse_dataset_to_dataframe(analysis.dataset_id, analysis.tenant_id, analysis.workspace_id, self.db)
                    
                    mappings = dataset.mappings or {}
                    def get_col_by_role(role_name):
                        for col, role in mappings.items():
                            if role == role_name:
                                return col
                        return None
                    
                    supplier_id_col = get_col_by_role("supplier_id") or "supplier_id"
                    carbon_col = "carbon_emissions" if "carbon_emissions" in df.columns else (get_col_by_role("carbon_emissions") or "emissions_kg")
                    
                    df[carbon_col] = pd.to_numeric(df[carbon_col], errors="coerce").fillna(0.0)
                    supplier_totals = df.groupby(supplier_id_col)[carbon_col].sum().to_dict()
                    
                    lines = []
                    for sup_id, val in sorted(supplier_totals.items()):
                        lines.append(f"{sup_id} = {int(val)} kg")
                    grounded_response = "\n".join(lines)
                    is_grounded_query = True
                except Exception as e:
                    logger.warning(f"Failed to calculate supplier emissions dynamically: {e}")

            # 3. Highest Transport Mode
            elif "highest" in uq_clean and "transport" in uq_clean and "mode" in uq_clean:
                try:
                    import pandas as pd
                    from app.core.ocel_parser import parse_dataset_to_dataframe
                    from app.models.models import Dataset
                    
                    analysis = self.db.query(ProcessAnalysis).filter(ProcessAnalysis.id == analysis_id).first()
                    dataset = self.db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
                    df = parse_dataset_to_dataframe(analysis.dataset_id, analysis.tenant_id, analysis.workspace_id, self.db)
                    
                    mappings = dataset.mappings or {}
                    def get_col_by_role(role_name):
                        for col, role in mappings.items():
                            if role == role_name:
                                return col
                        return None
                        
                    transport_mode_col = get_col_by_role("transport_mode") or "transport_mode"
                    carbon_col = "carbon_emissions" if "carbon_emissions" in df.columns else (get_col_by_role("carbon_emissions") or "emissions_kg")
                    
                    df[carbon_col] = pd.to_numeric(df[carbon_col], errors="coerce").fillna(0.0)
                    transport_totals = df.groupby(transport_mode_col)[carbon_col].sum().to_dict()
                    total_val = sum(transport_totals.values())
                    
                    highest_mode = max(transport_totals, key=transport_totals.get)
                    highest_val = transport_totals[highest_mode]
                    pct = (highest_val / total_val * 100) if total_val > 0 else 0.0
                    
                    grounded_response = f"{highest_mode} = {int(highest_val)} kg\n{pct:.2f}%"
                    is_grounded_query = True
                except Exception as e:
                    logger.warning(f"Failed to calculate highest transport mode dynamically: {e}")

            # 4. Case Count
            elif "how many cases" in uq_clean or "case count" in uq_clean:
                try:
                    import pandas as pd
                    from app.core.ocel_parser import parse_dataset_to_dataframe
                    from app.models.models import Dataset
                    
                    analysis = self.db.query(ProcessAnalysis).filter(ProcessAnalysis.id == analysis_id).first()
                    dataset = self.db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
                    df = parse_dataset_to_dataframe(analysis.dataset_id, analysis.tenant_id, analysis.workspace_id, self.db)
                    
                    mappings = dataset.mappings or {}
                    def get_col_by_role(role_name):
                        for col, role in mappings.items():
                            if role == role_name:
                                return col
                        return None
                        
                    case_id_col = "case:concept:name" if "case:concept:name" in df.columns else (get_col_by_role("case_id") or "case_id")
                    cases_count = df[case_id_col].nunique()
                    grounded_response = f"{cases_count}"
                    is_grounded_query = True
                except Exception as e:
                    logger.warning(f"Failed to calculate case count dynamically: {e}")

            # 6. Highest Emission Shipment (Bug 8 fix: was missing, causing LLM fallback)
            elif "highest" in uq_clean and "shipment" in uq_clean:
                try:
                    import pandas as pd
                    from app.core.ocel_parser import parse_dataset_to_dataframe
                    from app.models.models import Dataset

                    analysis = self.db.query(ProcessAnalysis).filter(ProcessAnalysis.id == analysis_id).first()
                    dataset = self.db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
                    df = parse_dataset_to_dataframe(analysis.dataset_id, analysis.tenant_id, analysis.workspace_id, self.db)

                    mappings = dataset.mappings or {}
                    def get_col_by_role(role_name):
                        for col, role in mappings.items():
                            if role == role_name:
                                return col
                        return None

                    shipment_id_col = get_col_by_role("shipment_id") or "shipment_id"
                    carbon_col = "carbon_emissions" if "carbon_emissions" in df.columns else (get_col_by_role("carbon_emissions") or "emissions_kg")

                    df[carbon_col] = pd.to_numeric(df[carbon_col], errors="coerce").fillna(0.0)
                    if shipment_id_col in df.columns:
                        shipment_totals = df.groupby(shipment_id_col)[carbon_col].sum().to_dict()
                        highest_sh = max(shipment_totals, key=shipment_totals.get)
                        highest_val = shipment_totals[highest_sh]
                        lines = [f"{sh_id} = {int(val)} kg" for sh_id, val in sorted(shipment_totals.items())]
                        lines.append(f"Highest: {highest_sh} = {int(highest_val)} kg")
                        grounded_response = "\n".join(lines)
                    else:
                        grounded_response = "No shipment_id column found in dataset."
                    is_grounded_query = True
                except Exception as e:
                    logger.warning(f"Failed to calculate highest shipment dynamically: {e}")

        # Quality validation check helper
        def validate_quality(text: str) -> bool:
            # We want to check for the 6 structured headings
            required_sections = [
                "1. Executive Summary",
                "2. Root Causes",
                "3. Business Impact",
                "4. Recommended Actions",
                "5. Expected Improvement",
                "6. Confidence Level"
            ]
            for sec in required_sections:
                if sec not in text:
                    return False
            return True

        if is_grounded_query:
            response_text = grounded_response
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
        else:
            response_text = ai_provider.generate(prompt)
            response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()

            # Quality gate validation & repair attempt
            if not validate_quality(response_text):
                logger.info("Quality gate validation failed. Initiating auto-repair re-prompt attempt (MAX_RESPONSE_REPAIR_ATTEMPTS = 1)")
                repair_prompt = (
                    f"{prompt}\n\n[WARNING: Previous response was malformed. You MUST structure your answer with EXACTLY the 6 numbered headers requested: "
                    "1. Executive Summary, 2. Root Causes, 3. Business Impact, 4. Recommended Actions, 5. Expected Improvement, 6. Confidence Level. "
                    "Do not include conversational preamble.]"
                )
                response_text = ai_provider.generate(repair_prompt)
                response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()

            execution_time_ms = int((time.monotonic() - start_time) * 1000)

        # 7. Response Size Protection (truncate to 8000 chars)
        response_text = response_text[:MAX_AI_RESPONSE_CHARS]

        # 8. Token Accounting
        token_count = math.ceil((len(prompt) + len(response_text)) / 4)
        if token_count < 0:
            token_count = 0

        # 9. Extended Metadata
        execution_timestamp = datetime.utcnow().isoformat() + "Z"
        metadata = {
            "provider": "ollama",
            "model": selected_model,
            "prompt_style": prompt_style,
            "response_style": response_style,
            "quality_mode": quality_mode,
            "latency_ms": execution_time_ms,
            "execution_timestamp": execution_timestamp,
            "prompt_version": AI_PROMPT_VERSION
        }

        # 10. Persistence (Always append/insert new)
        copilot_response = AiCopilotResponse(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            entity_id=entity_id,
            provider="OLLAMA",
            model_name=selected_model,
            request_type=req_type_str,
            prompt_version=AI_PROMPT_VERSION,
            prompt_hash=prompt_hash,
            response_text=response_text,
            token_count=token_count,
            execution_time_ms=execution_time_ms,
            response_metadata=metadata,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        persisted_response = self.repository.create(copilot_response)

        # 11. Audit Event Logging
        details_payload = {
            "request_type": req_type_str,
            "provider": "OLLAMA",
            "entity_id": str(entity_id),
            "response_id": str(persisted_response.id),
            "model_name": selected_model
        }
        log_activity(
            self.db,
            user_id=user_id,
            action="copilot_response_generated",
            tenant_id=tenant_id,
            details=json.dumps(details_payload)
        )

        return persisted_response

    def list_responses(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        request_type: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[AiCopilotResponse]:
        return self.repository.list_responses(
            tenant_id=tenant_id,
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

    def count_responses(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        request_type: Optional[str] = None,
        provider: Optional[str] = None
    ) -> int:
        return self.repository.count_responses(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            request_type=request_type,
            provider=provider
        )
