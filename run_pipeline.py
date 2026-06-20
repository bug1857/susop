import os
import sys
import uuid
import json
import hashlib
from datetime import datetime, timezone

# Ensure path is set to backend
os.chdir("/Users/rudrapratapsingh/Desktop/newpro/backend")
sys.path.append("/Users/rudrapratapsingh/Desktop/newpro/backend")
os.environ["USE_SQLITE"] = "true"

from app.core.database import SessionLocal
from app.models.models import (
    ProcessAnalysis,
    ScenarioSimulation,
    ScenarioType,
    EsgFramework,
    EsgKpiDefinition,
    EsgScoringProfile,
    FrameworkMapping,
    EsgKpiValue,
    EsgEvidence,
    EsgScore
)
from app.services.ocel_service import OcelGenerationService
from app.services.object_conformance_service import ObjectConformanceService
from app.services.object_carbon_service import ObjectCarbonAttributionService
from app.services.object_interaction_service import ObjectInteractionService
from app.services.object_simulation_service import ObjectSimulationService
from app.services.ocel_interoperability_service import OcelInteroperabilityService
from app.services.carbon_fitness_service import CarbonFitnessService
from app.services.sustainability_conformance_service import SustainabilityConformanceService
from app.services.process_optimization_service import ProcessOptimizationService
from app.services.recommendation_engine import RecommendationEngine
from app.services.green_rerouting_service import GreenReroutingService
from app.services.esg_kpi_service import EsgKpiService
from app.services.esg_scoring_service import EsgScoringService
from app.services.esg_evidence_service import EsgEvidenceService
from app.services.esg_framework_service import EsgFrameworkService

def run():
    db = SessionLocal()
    try:
        # 1. Fetch latest completed ProcessAnalysis
        analysis = db.query(ProcessAnalysis).filter(
            ProcessAnalysis.status == "completed",
            ProcessAnalysis.is_deleted == False
        ).order_by(ProcessAnalysis.created_at.desc()).first()

        if not analysis:
            print("[-] No completed process analysis found in database. Ingest a log file first.")
            return

        analysis_id = analysis.id
        tenant_id = analysis.tenant_id
        workspace_id = analysis.workspace_id
        project_id = analysis.project_id

        print(f"[+] Found active Process Analysis:")
        print(f"    Analysis ID:  {analysis_id}")
        print(f"    Tenant ID:    {tenant_id}")
        print(f"    Workspace ID: {workspace_id}")
        print(f"    Project ID:   {project_id}")

        # 2. Run OCPM Upstream Pipelines
        print("\n[~] Running OCEL 2.0 Generation...")
        ocel_res = OcelGenerationService(db).generate_and_persist(analysis_id)
        print(f"[+] Done: Version v{ocel_res.get('ocel_version')} generated.")

        print("\n[~] Running Object Conformance...")
        conf_res = ObjectConformanceService(db).generate_and_persist(analysis_id)
        print(f"[+] Done: Version v{conf_res.get('object_conformance_version')} generated.")

        print("\n[~] Running Object Carbon Attribution...")
        carbon_res = ObjectCarbonAttributionService(db).generate_and_persist(analysis_id)
        print(f"[+] Done: Version v{carbon_res.get('object_carbon_version')} generated.")
        actual_emissions = carbon_res.get("total_object_emissions", 0.0)

        print("\n[~] Running Object Interaction Analysis...")
        inter_res = ObjectInteractionService(db).generate_and_persist(analysis_id)
        print(f"[+] Done: Version v{inter_res.get('object_interaction_version')} generated.")

        print("\n[~] Running Object Simulation...")
        sim_res = ObjectSimulationService(db).generate_and_persist(analysis_id)
        print(f"[+] Done: Version v{sim_res.get('simulation_version')} generated.")

        print("\n[~] Running OCEL Interoperability Export & Import roundtrip...")
        interop_service = OcelInteroperabilityService(db)
        wrapper = interop_service.export_ocel_wrapper(analysis_id)
        import_res = interop_service.import_ocel(wrapper, analysis_id, user_context={})
        print(f"[+] Done: Imported version v{import_res.get('import_version')}.")

        print("\n[~] Running Carbon Fitness Calculation...")
        fit_service = CarbonFitnessService(db)
        # Compute dynamic carbon fitness
        fit_service.calculate_carbon_fitness(analysis_id, tenant_id, actual_emissions)
        print(f"[+] Done: Carbon fitness computed and updated.")

        print("\n[~] Running Sustainability Conformance...")
        scon_res = SustainabilityConformanceService(db).generate_and_persist(analysis_id)
        print(f"[+] Done: Sustainability Conformance v{scon_res.get('scon_version')} generated.")

        print("\n[~] Running Process Optimization...")
        ProcessOptimizationService(db).generate_and_persist(analysis_id)
        print(f"[+] Done: Process Optimization recommendations generated.")

        print("\n[~] Running Green Rerouting...")
        GreenReroutingService(db).generate_and_persist(analysis_id)
        print(f"[+] Done: Rerouting pathways updated.")

        print("\n[~] Running Recommendation Center...")
        RecommendationEngine(db).generate_and_persist(analysis_id)
        print(f"[+] Done: AI Insights & Recommendations updated.")

        # 3. Seed ESG Frameworks, Mappings, KPIs & Scores
        print("\n[~] Seeding ESG Regulatory Frameworks (BRSR & GRI)...")
        framework_service = EsgFrameworkService(db)
        
        brsr = db.query(EsgFramework).filter(EsgFramework.framework_name == "BRSR").first()
        if not brsr:
            brsr = framework_service.create_framework({
                "framework_name": "BRSR",
                "framework_version": "2026",
                "description": "Business Responsibility and Sustainability Reporting"
            })
            print(f"[+] Created BRSR Framework ID: {brsr.id}")
        else:
            print("[~] BRSR Framework already exists.")

        gri = db.query(EsgFramework).filter(EsgFramework.framework_name == "GRI").first()
        if not gri:
            gri = framework_service.create_framework({
                "framework_name": "GRI",
                "framework_version": "301",
                "description": "Global Reporting Initiative Standard"
            })
            print(f"[+] Created GRI Framework ID: {gri.id}")
        else:
            print("[~] GRI Framework already exists.")

        print("\n[~] Seeding ESG KPI Definitions...")
        kpi_service = EsgKpiService(db)
        
        # Env KPI Definition
        kpi_env = db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.kpi_code == "ENV-CO2-S1",
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_deleted == False
        ).first()
        if not kpi_env:
            kpi_env = kpi_service.create_kpi_definition(tenant_id, uuid.UUID("00000000-0000-0000-0000-00000000000a"), {
                "kpi_code": "ENV-CO2-S1",
                "version": 1,
                "name": "Scope 1 Direct Carbon Footprint",
                "category": "Environmental",
                "unit": "tCO2e",
                "source_type": "automated_process",
                "description": "Direct carbon footprint from automated process mining carbon attribution ledger.",
                "calculation_method": {"target": 10000.0, "direction": "minimize"},
                "effective_from": "2025-01-01T00:00:00Z"
            })
            print(f"[+] Seeded Environmental KPI Definition: {kpi_env.kpi_code}")
        else:
            print("[~] Environmental KPI already exists.")

        # Social KPI Definition
        kpi_soc = db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.kpi_code == "SOC-DIV-GE",
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_deleted == False
        ).first()
        if not kpi_soc:
            kpi_soc = kpi_service.create_kpi_definition(tenant_id, uuid.UUID("00000000-0000-0000-0000-00000000000a"), {
                "kpi_code": "SOC-DIV-GE",
                "version": 1,
                "name": "Gender Diversity Ratio",
                "category": "Social",
                "unit": "%",
                "source_type": "manual_entry",
                "description": "Ratio of female employees in administrative and operational departments.",
                "calculation_method": {"target": 40.0, "direction": "maximize"},
                "effective_from": "2025-01-01T00:00:00Z"
            })
            print(f"[+] Seeded Social KPI Definition: {kpi_soc.kpi_code}")
        else:
            print("[~] Social KPI already exists.")

        # Governance KPI Definition
        kpi_gov = db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.kpi_code == "GOV-COMP-TR",
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_deleted == False
        ).first()
        if not kpi_gov:
            kpi_gov = kpi_service.create_kpi_definition(tenant_id, uuid.UUID("00000000-0000-0000-0000-00000000000a"), {
                "kpi_code": "GOV-COMP-TR",
                "version": 1,
                "name": "Compliance Training Rate",
                "category": "Governance",
                "unit": "%",
                "source_type": "manual_entry",
                "description": "Percentage of resources completing compliance and anti-bribery training.",
                "calculation_method": {"target": 95.0, "direction": "maximize"},
                "effective_from": "2025-01-01T00:00:00Z"
            })
            print(f"[+] Seeded Governance KPI Definition: {kpi_gov.kpi_code}")
        else:
            print("[~] Governance KPI already exists.")

        print("\n[~] Seeding ESG KPI Mappings to Regulatory Frameworks...")
        # Map ENV-CO2-S1 to BRSR Principle 6
        exists_map1 = db.query(FrameworkMapping).filter(
            FrameworkMapping.framework_id == brsr.id,
            FrameworkMapping.kpi_definition_id == kpi_env.id
        ).first()
        if not exists_map1:
            framework_service.create_mapping({
                "framework_id": brsr.id,
                "kpi_definition_id": kpi_env.id,
                "framework_section": "Section C",
                "framework_principle": "Principle 6",
                "framework_question": "Essential-Q5",
                "reporting_category": "Essential Indicators"
            })
            print("[+] Mapped ENV-CO2-S1 to BRSR Section C Principle 6.")

        # Map SOC-DIV-GE to BRSR Principle 3
        exists_map2 = db.query(FrameworkMapping).filter(
            FrameworkMapping.framework_id == brsr.id,
            FrameworkMapping.kpi_definition_id == kpi_soc.id
        ).first()
        if not exists_map2:
            framework_service.create_mapping({
                "framework_id": brsr.id,
                "kpi_definition_id": kpi_soc.id,
                "framework_section": "Section B",
                "framework_principle": "Principle 3",
                "framework_question": "Key-Q2",
                "reporting_category": "Essential Indicators"
            })
            print("[+] Mapped SOC-DIV-GE to BRSR Section B Principle 3.")

        print("\n[~] Seeding ESG Scoring Profile...")
        scoring_service = EsgScoringService(db)
        profile = db.query(EsgScoringProfile).filter(
            EsgScoringProfile.tenant_id == tenant_id,
            EsgScoringProfile.is_active == True,
            EsgScoringProfile.is_deleted == False
        ).first()
        if not profile:
            profile = scoring_service.configure_scoring_profile(tenant_id, uuid.UUID("00000000-0000-0000-0000-00000000000a"), {
                "name": "Standard Baseline Profile (Default)",
                "environmental_weight": 0.4,
                "social_weight": 0.3,
                "governance_weight": 0.3,
                "kpi_weights": {
                    "ENV-CO2-S1": 1.0,
                    "SOC-DIV-GE": 1.0,
                    "GOV-COMP-TR": 1.0
                }
            })
            print(f"[+] Created active ESG Scoring Profile: {profile.name}")
        else:
            print(f"[~] Active ESG Scoring Profile already exists: {profile.name}")

        print("\n[~] Seeding ESG KPI Values & Evidence...")
        # Record actual Env value (convert kg to tonnes CO2e: e.g. 2,428,443 kg -> 2428.4 tCO2e)
        env_tonnes = actual_emissions / 1000.0
        
        # Seed values for multiple periods to generate progression trend
        periods = ["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2", "2026"]
        
        for period in periods:
            # Check if KPI value exists
            kpi_val = db.query(EsgKpiValue).filter(
                EsgKpiValue.kpi_definition_id == kpi_env.id,
                EsgKpiValue.workspace_id == workspace_id,
                EsgKpiValue.period == period,
                EsgKpiValue.is_deleted == False
            ).first()
            
            if not kpi_val:
                # Add some simulated trends (older quarters had higher emissions)
                multiplier = 1.3 - (periods.index(period) * 0.06)
                val_env = env_tonnes * multiplier
                val_soc = 42.0 + (periods.index(period) * 0.8)
                val_gov = 88.0 + (periods.index(period) * 1.1)

                # Record Environmental value
                kpi_val_env = kpi_service.record_kpi_value(tenant_id, uuid.UUID("00000000-0000-0000-0000-00000000000a"), {
                    "kpi_definition_id": kpi_env.id,
                    "workspace_id": workspace_id,
                    "project_id": project_id,
                    "period": period,
                    "value": float(val_env),
                    "is_manual": False
                })

                # Register cryptographic evidence linking Env value to process analysis & carbon run
                evidence_service = EsgEvidenceService(db)
                evidence_service.register_evidence(tenant_id, uuid.UUID("00000000-0000-0000-0000-00000000000a"), {
                    "kpi_value_id": kpi_val_env.id,
                    "source_description": f"Automated carbon footprint aggregate for {period} from Carbon Attribution ledger.",
                    "source_entity_type": "process_analysis",
                    "source_entity_id": analysis_id,
                    "cryptographic_hash": hashlib.sha256(f"{analysis_id}-{period}-{val_env}".encode()).hexdigest(),
                    "calculation_steps": {"sum_emissions_kg": actual_emissions * multiplier, "conversion_factor": 0.001},
                    "lineage_path": {
                        "dataset_id": str(analysis.dataset_id),
                        "process_analysis_id": str(analysis_id),
                        "carbon_attribution_id": str(carbon_res.get("object_carbon_run_id", uuid.uuid4()))
                    }
                })

                # Record Social value
                kpi_service.record_kpi_value(tenant_id, uuid.UUID("00000000-0000-0000-0000-00000000000a"), {
                    "kpi_definition_id": kpi_soc.id,
                    "workspace_id": workspace_id,
                    "project_id": project_id,
                    "period": period,
                    "value": float(val_soc),
                    "is_manual": True
                })

                # Record Governance value
                kpi_service.record_kpi_value(tenant_id, uuid.UUID("00000000-0000-0000-0000-00000000000a"), {
                    "kpi_definition_id": kpi_gov.id,
                    "workspace_id": workspace_id,
                    "project_id": project_id,
                    "period": period,
                    "value": float(val_gov),
                    "is_manual": True
                })

                print(f"[+] Recorded ESG values & evidence for period {period}.")
            
            # Recalculate Rollup Score for this period
            scoring_service.calculate_esg_score(workspace_id, period, tenant_id, uuid.UUID("00000000-0000-0000-0000-00000000000a"))
            print(f"[+] Calculated ESG Rollup Score for period {period}.")

        print("\n[~] Running AI Insight Generation...")
        from app.services.ai_insight_service import AiInsightService
        insight_service = AiInsightService(db)
        insights_res = insight_service.generate_insights(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            analysis_id=analysis_id,
            user_id=uuid.UUID("00000000-0000-0000-0000-00000000000a")
        )
        print(f"[+] Done: {len(insights_res)} AI Insights generated.")

        print("\n[+] SUCCESS! Pipeline complete. Refresh the website pages to view the rich dynamic data.")
        
    finally:
        db.close()

if __name__ == "__main__":
    run()
