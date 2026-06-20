import os
import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from app.models.models import (
    Workspace,
    Project,
    Organization,
    ProcessAnalysis,
    Dataset,
    ConformanceResult,
    ConformanceDeviation,
    CarbonAttribution,
    EmissionHotspot,
    EsgScore,
    ProcessVariant,
    ProcessBottleneck
)
from app.core.ingestion import detect_delimiter

REPORTS_DIR = "/Users/rudrapratapsingh/Desktop/newpro/backend/storage/reports"

class BRSRService:
    def __init__(self, db: Session):
        self.db = db
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def get_next_version(self, analysis_id: uuid.UUID) -> int:
        count = 0
        if not os.path.exists(REPORTS_DIR):
            return 1
        for f in os.listdir(REPORTS_DIR):
            if f.startswith("brsr_") and f.endswith(".json"):
                try:
                    with open(os.path.join(REPORTS_DIR, f), "r") as file:
                        data = json.load(file)
                        if data.get("analysis_id") == str(analysis_id):
                            count += 1
                except Exception:
                    pass
        return count + 1

    def list_versions_metadata(self, analysis_id: uuid.UUID) -> list:
        history = []
        if not os.path.exists(REPORTS_DIR):
            return history
        for f in os.listdir(REPORTS_DIR):
            if f.startswith("brsr_") and f.endswith(".json"):
                try:
                    with open(os.path.join(REPORTS_DIR, f), "r") as file:
                        data = json.load(file)
                        if data.get("analysis_id") == str(analysis_id):
                            history.append({
                                "report_id": data.get("report_id"),
                                "report_version": data.get("report_version"),
                                "generated_at": data.get("generated_at"),
                                "status": data.get("status"),
                                "completeness_score": data.get("report_completeness_score", 0),
                                "audit_readiness": data.get("audit_readiness", "Insufficient Evidence"),
                                "generated_from_analysis_version": data.get("generated_from_analysis_version", 1),
                                "total_deviations": data.get("section_b", {}).get("deviation_summary", {}).get("total_deviations", 0),
                                "total_emissions_kg": data.get("section_c", {}).get("total_actual_emissions_kg", 0.0)
                            })
                except Exception:
                    pass
        # Sort newest first
        history.sort(key=lambda x: x["report_version"], reverse=True)
        return history

    def generate_report(self, analysis_id: uuid.UUID) -> dict:
        analysis = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == analysis_id,
            ProcessAnalysis.is_deleted == False
        ).first()
        if not analysis:
            raise ValueError("Analysis not found")

        workspace = self.db.query(Workspace).filter(Workspace.id == analysis.workspace_id).first()
        project = self.db.query(Project).filter(Project.id == analysis.project_id).first()
        organization = self.db.query(Organization).filter(Organization.id == analysis.tenant_id).first()
        dataset = self.db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()

        # Gather Carbon Fitness and Sustainability Conformance results
        from app.services.carbon_fitness_service import CarbonFitnessService
        carbon_fitness_data = CarbonFitnessService(self.db).get_latest(analysis_id) or {}
        
        from app.services.sustainability_conformance_service import SustainabilityConformanceService
        sus_conf_data = SustainabilityConformanceService(self.db).get_latest(analysis_id) or {}

        # Gather carbon hotspots & deviations
        deviations = self.db.query(ConformanceDeviation).filter(
            ConformanceDeviation.analysis_id == analysis_id
        ).all()

        hotspots = self.db.query(EmissionHotspot).filter(
            EmissionHotspot.analysis_id == analysis_id
        ).all()

        # Process variant and wait-time statistics
        variants = self.db.query(ProcessVariant).filter(
            ProcessVariant.analysis_id == analysis_id,
            ProcessVariant.is_deleted == False
        ).all()

        bottlenecks = self.db.query(ProcessBottleneck).filter(
            ProcessBottleneck.analysis_id == analysis_id,
            ProcessBottleneck.is_deleted == False
        ).all()

        # Gather ESG score
        esg_score = self.db.query(EsgScore).filter(
            EsgScore.workspace_id == analysis.workspace_id,
            EsgScore.is_deleted == False
        ).order_by(EsgScore.calculated_at.desc()).first()

        # Seeding metrics from CSV parsing
        total_energy = 0.0
        total_water = 0.0
        total_waste = 0.0
        suppliers_raw = []

        if dataset and os.path.exists(dataset.original_file_path):
            try:
                delim = detect_delimiter(dataset.original_file_path)
                df = pd.read_csv(dataset.original_file_path, sep=delim)
                mappings = dataset.mappings or {}
                role_to_header = {role: header for header, role in mappings.items()}

                energy_col = role_to_header.get("energy_kwh")
                water_col = role_to_header.get("water_liters")
                waste_col = role_to_header.get("waste_kg")

                if energy_col and energy_col in df.columns:
                    total_energy = float(pd.to_numeric(df[energy_col], errors="coerce").sum())
                if water_col and water_col in df.columns:
                    total_water = float(pd.to_numeric(df[water_col], errors="coerce").sum())
                if waste_col and waste_col in df.columns:
                    total_waste = float(pd.to_numeric(df[waste_col], errors="coerce").sum())

                # Supplier parsing
                supplier_id_col = role_to_header.get("supplier_id")
                supplier_name_col = role_to_header.get("supplier_name")
                carbon_col = role_to_header.get("carbon_emissions")
                cost_col = role_to_header.get("cost")
                risk_col = role_to_header.get("risk_level")
                country_col = role_to_header.get("supplier_country")

                if supplier_id_col and supplier_id_col in df.columns:
                    name_col = supplier_name_col if (supplier_name_col and supplier_name_col in df.columns) else supplier_id_col
                    cost_c = cost_col if (cost_col and cost_col in df.columns) else None
                    carb_c = carbon_col if (carbon_col and carbon_col in df.columns) else None
                    risk_c = risk_col if (risk_col and risk_col in df.columns) else None
                    country_c = country_col if (country_col and country_col in df.columns) else None

                    grouped = df.groupby(supplier_id_col)
                    for supp_id, group in grouped:
                        supp_name = str(group[name_col].dropna().iloc[0]) if not group[name_col].dropna().empty else str(supp_id)
                        supp_country = str(group[country_c].dropna().iloc[0]) if (country_c and not group[country_c].dropna().empty) else "Unknown"
                        supp_emissions = float(pd.to_numeric(group[carb_c], errors="coerce").sum()) if carb_c else 0.0
                        supp_spend = float(pd.to_numeric(group[cost_c], errors="coerce").sum()) if cost_c else 0.0
                        
                        if risk_c and not group[risk_c].dropna().empty:
                            supp_risk = str(group[risk_c].value_counts().index[0])
                        else:
                            supp_risk = "Low"

                        # Same esg score logic as ingestion.py
                        score = 80
                        if supp_risk == "High":
                            score -= 20
                        elif supp_risk == "Medium":
                            score -= 10
                        if supp_emissions > 50000:
                            score -= 20
                        elif supp_emissions > 10000:
                            score -= 10
                        score = max(10, min(95, score))

                        suppliers_raw.append({
                            "supplier_id": str(supp_id),
                            "supplier_name": supp_name,
                            "supplier_country": supp_country,
                            "emissions": supp_emissions,
                            "spend": supp_spend,
                            "risk_level": supp_risk,
                            "esg_score": score / 100.0
                        })
            except Exception as e:
                import traceback
                print(f"Error parsing dataset for BRSR: {e}")
                traceback.print_exc()

        # Standardize UTC format without trailing malformations
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Build Section A: General
        section_a = {
            "organization_id": str(organization.id) if organization else None,
            "organization_name": organization.name if organization else "Unknown Organization",
            "workspace_id": str(workspace.id) if workspace else None,
            "workspace_name": workspace.name if workspace else "Unknown Workspace",
            "project_id": str(project.id) if project else None,
            "project_name": project.name if project else "Unknown Project",
            "dataset_id": str(dataset.id) if dataset else None,
            "dataset_name": dataset.name if dataset else "Unknown Dataset",
            "reporting_period": esg_score.period if esg_score else "2026",
            "report_boundary": "Operational Control Boundaries"
        }

        # Build Section B: Management & Process Disclosures
        # Bug 2 fix: read actual trace counts from ConformanceResult instead of hardcoding 0
        latest_conf_result = self.db.query(ConformanceResult).filter(
            ConformanceResult.analysis_id == analysis_id
        ).order_by(ConformanceResult.created_at.desc()).first()
        total_trace_count = int(latest_conf_result.diagnostic_trace_count) if latest_conf_result else 0
        non_conforming_trace_count = int(latest_conf_result.non_conforming_trace_count) if latest_conf_result else 0

        section_b = {
            "compliance_score": sus_conf_data.get("process_fitness", 0.0),
            "carbon_fitness": carbon_fitness_data.get("carbon_fitness", 0.0),
            "actual_emissions": carbon_fitness_data.get("actual_emissions_kg", 0.0),
            "conformance_method": "Token-Based Replay (TBR)",
            "total_trace_count": total_trace_count,
            "non_conforming_trace_count": non_conforming_trace_count,
            "reference_model_id": carbon_fitness_data.get("source_reference_model_version"),
            "reference_model_version": carbon_fitness_data.get("source_reference_model_version", 1),
            "deviations_count": len(deviations),
            "deviations": [
                {
                    "case_id": d.case_id,
                    "activity_name": d.activity_name,
                    "deviation_type": d.deviation_type,
                    "expected_transition": d.expected_transition,
                    "actual_transition": d.actual_transition,
                    "severity": d.severity
                }
                for d in deviations[:15]
            ],
            "bottlenecks": [
                {
                    "activity_name": b.activity_name,
                    "average_wait_time_sec": b.average_wait_time,
                    "occurrence_count": b.occurrence_count
                }
                for b in bottlenecks
            ],
            "bottleneck_summary": {
                "total_bottlenecks": len(bottlenecks),
                "activities_impacted": len(set(b.activity_name for b in bottlenecks))
            },
            "variant_statistics": {
                "total_variants": len(variants),
                "variant_distribution": [{"variant_id": str(v.id), "frequency": v.frequency, "percentage": v.percentage} for v in variants[:10]]
            },
            "deviation_summary": {
                "total_deviations": len(deviations),
                "by_severity": {
                    "High": len([d for d in deviations if d.severity == "High"]),
                    "Medium": len([d for d in deviations if d.severity == "Medium"]),
                    "Low": len([d for d in deviations if d.severity == "Low"])
                }
            }
        }

        # Build Section C: Principle-wise Performance
        supplier_esg_rankings = sorted(suppliers_raw, key=lambda x: x["esg_score"], reverse=True)[:5]
        supplier_risk_rankings = sorted(suppliers_raw, key=lambda x: (3 if x["risk_level"] == "High" else (2 if x["risk_level"] == "Medium" else 1), x["spend"]), reverse=True)[:5]

        section_c = {
            "esg_overall_score": esg_score.overall_score if esg_score else 0.0,
            "environmental_score": esg_score.environmental_score if esg_score else 0.0,
            "social_score": esg_score.social_score if esg_score else 0.0,
            "governance_score": esg_score.governance_score if esg_score else 0.0,
            "completeness_score": esg_score.completeness_score if esg_score else 0.0,
            
            "total_energy_consumption_kwh": total_energy,
            "energy_kwh": total_energy,
            
            "total_water_consumption_liters": total_water,
            "water_consumption": total_water,
            
            "total_waste_generation_kg": total_waste,
            "waste_generated": total_waste,
            
            "total_actual_emissions_kg": carbon_fitness_data.get("actual_emissions_kg", 0.0),
            "carbon_budget_limit_kg": carbon_fitness_data.get("carbon_budget_kg", 0.0),
            "carbon_budget_exceeded": carbon_fitness_data.get("budget_utilization_pct", 0.0) > 100.0,  # Bug 6 fix: was > 1.0 (1%)
            
            "total_suppliers_tracked": len(suppliers_raw),
            "supplier_esg_rankings": supplier_esg_rankings,
            "supplier_risk_rankings": supplier_risk_rankings,
            "supplier_esg_risk_rankings": supplier_risk_rankings,
            
            "carbon_hotspots": [
                {
                    "activity_name": h.activity_name,
                    "emissions_kg": h.emissions,
                    "contribution_percentage": h.contribution_percentage,
                    "severity": h.severity
                }
                for h in hotspots
            ]
        }

        # Build Section D: Traceability
        section_d = {
            "traceability_matrix": [
                {
                    "brsr_metric": "ESG Score", "originating_engine": "ESG Scoring Engine", "database_source": "esg_scores table", "reference_field": "overall_score",
                    "report_field": "esg_overall_score", "source_engine": "ESG Scoring Engine", "source_metric": "overall_score", "source_endpoint": "/api/v1/esg/scores"
                },
                {
                    "brsr_metric": "Environmental Score", "originating_engine": "ESG Scoring Engine", "database_source": "esg_scores table", "reference_field": "environmental_score",
                    "report_field": "environmental_score", "source_engine": "ESG Scoring Engine", "source_metric": "environmental_score", "source_endpoint": "/api/v1/esg/scores"
                },
                {
                    "brsr_metric": "Total Emissions", "originating_engine": "Carbon Attribution Engine", "database_source": "conformance_results table", "reference_field": "actual_emissions",
                    "report_field": "total_actual_emissions_kg", "source_engine": "Carbon Attribution Engine", "source_metric": "actual_emissions", "source_endpoint": "/api/process/{analysis_id}/conformance"
                },
                {
                    "brsr_metric": "Carbon Fitness Score", "originating_engine": "Carbon Fitness Engine", "database_source": "conformance_results table", "reference_field": "carbon_fitness_score",
                    "report_field": "carbon_fitness", "source_engine": "Carbon Fitness Engine", "source_metric": "carbon_fitness_score", "source_endpoint": "/api/process/{analysis_id}/conformance"
                },
                {
                    "brsr_metric": "Compliance / Fitness Score", "originating_engine": "Conformance Check Engine", "database_source": "conformance_results table", "reference_field": "fitness_score",
                    "report_field": "compliance_score", "source_engine": "Conformance Check Engine", "source_metric": "fitness_score", "source_endpoint": "/api/process/{analysis_id}/conformance"
                },
                {
                    "brsr_metric": "Energy Consumption", "originating_engine": "Ingestion Pipeline", "database_source": "sustainocpm_enterprise_30000_events.csv", "reference_field": "energy_kwh mappings",
                    "report_field": "total_energy_consumption_kwh", "source_engine": "Ingestion Pipeline", "source_metric": "energy_kwh", "source_endpoint": "/api/ingestion/datasets/{dataset_id}/sustainability-metrics"
                },
                {
                    "brsr_metric": "Water Consumption", "originating_engine": "Ingestion Pipeline", "database_source": "sustainocpm_enterprise_30000_events.csv", "reference_field": "water_liters mappings",
                    "report_field": "total_water_consumption_liters", "source_engine": "Ingestion Pipeline", "source_metric": "water_liters", "source_endpoint": "/api/ingestion/datasets/{dataset_id}/sustainability-metrics"
                },
                {
                    "brsr_metric": "Waste Generation", "originating_engine": "Ingestion Pipeline", "database_source": "sustainocpm_enterprise_30000_events.csv", "reference_field": "waste_kg mappings",
                    "report_field": "total_waste_generation_kg", "source_engine": "Ingestion Pipeline", "source_metric": "waste_kg", "source_endpoint": "/api/ingestion/datasets/{dataset_id}/sustainability-metrics"
                },
                {
                    "brsr_metric": "Supplier Risk Rankings", "originating_engine": "Supplier Intelligence", "database_source": "sustainocpm_enterprise_30000_events.csv", "reference_field": "supplier_id, risk_level",
                    "report_field": "supplier_esg_risk_rankings", "source_engine": "Supplier Intelligence", "source_metric": "supplier_id, risk_level", "source_endpoint": "/api/ingestion/datasets/{dataset_id}/sustainability-metrics"
                },
                {
                    "brsr_metric": "AI Recommendations", "originating_engine": "AI Recommendations Engine", "database_source": "ai_recommendations table", "reference_field": "estimated_emission_reduction",
                    "report_field": "recommendations", "source_engine": "AI Recommendations Engine", "source_metric": "estimated_emission_reduction", "source_endpoint": "/api/v1/copilot/generate"
                }
            ]
        }

        # DYNAMIC RECOMMENDATIONS POPULATION (Store ONLY in report payload, do NOT save to database)
        recs_payload = []
        
        # 2. Fitness / Conformance Checks
        fitness = sus_conf_data.get("process_fitness", 0.0)
        if fitness < 0.80:
            recs_payload.append({
                "id": str(uuid.uuid4()),
                "title": "Standardize compliance validation workflows",
                "description": f"Process compliance fitness is currently at {fitness*100:.1f}%. Implement automated checks for conformance deviations to enforce standardized execution paths and eliminate {len(deviations)} detected deviations.",
                "priority": "HIGH" if fitness < 0.8 else "MEDIUM",
                "estimated_emission_reduction": 10.0,
                "estimated_cost_reduction": 5.0,
                "confidence_score": 85.0
            })
            
        # Carbon fitness based recommendations
        carbon_fit = carbon_fitness_data.get("carbon_fitness", 0.0)
        budget_exceeded = carbon_fitness_data.get("budget_utilization_pct", 0.0) > 1.0
        if budget_exceeded or carbon_fit < 0.90:
            recs_payload.append({
                "id": str(uuid.uuid4()),
                "title": "Remediate carbon budget exceedance",
                "description": f"Carbon fitness is {carbon_fit*100:.1f}% and the allocated carbon budget is exceeded. Relocate emissions to lower-impact activities or enforce green routing.",
                "priority": "CRITICAL" if budget_exceeded else "HIGH",
                "estimated_emission_reduction": 25.0,
                "estimated_cost_reduction": 0.0,
                "confidence_score": 90.0
            })

        # 3. Bottlenecks
        if bottlenecks:
            worst_bot = max(bottlenecks, key=lambda x: x.average_wait_time)
            recs_payload.append({
                "id": str(uuid.uuid4()),
                "title": f"Reduce bottleneck wait times at {worst_bot.activity_name}",
                "description": f"Activity '{worst_bot.activity_name}' represents the largest process delay with an average wait time of {worst_bot.average_wait_time:.1f} seconds across {worst_bot.occurrence_count} occurrences. Reduce bottleneck wait times to lower idle emission overhead.",
                "priority": "HIGH" if worst_bot.average_wait_time > 600 else "MEDIUM",
                "estimated_emission_reduction": 5.0,
                "estimated_cost_reduction": 15.0,
                "confidence_score": 88.0
            })

        # 4. Carbon Hotspots
        if hotspots:
            worst_hot = max(hotspots, key=lambda x: x.emissions)
            recs_payload.append({
                "id": str(uuid.uuid4()),
                "title": f"Reduce emissions in {worst_hot.activity_name}",
                "description": f"Carbon hotspot identified at '{worst_hot.activity_name}' emitting {worst_hot.emissions:.1f} kg CO2e ({worst_hot.contribution_percentage:.1f}% of total). Transition to energy-efficient operations or green resources to mitigate emissions in this stage.",
                "priority": "CRITICAL" if worst_hot.contribution_percentage > 20.0 else "HIGH",
                "estimated_emission_reduction": 20.0,
                "estimated_cost_reduction": 5.0,
                "confidence_score": 87.0
            })

        # 5. Supplier Risk
        high_risk_suppliers = [s for s in suppliers_raw if s.get("risk_level") == "High"]
        if high_risk_suppliers:
            recs_payload.append({
                "id": str(uuid.uuid4()),
                "title": "Investigate supplier ESG risks",
                "description": f"Audited procurement logs identified high ESG risk profiles for {len(high_risk_suppliers)} supplier(s). Engage in supplier sustainability audits or select alternative vendors to improve carbon scores.",
                "priority": "HIGH",
                "estimated_emission_reduction": 15.0,
                "estimated_cost_reduction": 2.0,
                "confidence_score": 80.0
            })

        # 6. ESG overall
        esg_val = esg_score.overall_score if esg_score else 0.0
        if esg_val < 0.90:
            recs_payload.append({
                "id": str(uuid.uuid4()),
                "title": "Improve corporate ESG framework scores",
                "description": f"Overall ESG framework index is currently {esg_val*100:.1f}%. Strengthen social welfare tracking and corporate governance reporting to reach compliance targets.",
                "priority": "MEDIUM",
                "estimated_emission_reduction": 8.0,
                "estimated_cost_reduction": 4.0,
                "confidence_score": 82.0
            })

        if not recs_payload:
            recs_payload.append({
                "id": str(uuid.uuid4()),
                "title": "Establish sustainability reporting baseline",
                "description": "Initial data indicates conformance is within boundaries. Establish a baseline for continuous process mining and real-time carbon attribution tracking.",
                "priority": "LOW",
                "estimated_emission_reduction": 5.0,
                "estimated_cost_reduction": 5.0,
                "confidence_score": 95.0
            })

        # Calculate Completeness Score
        comp_a = 25 if (organization and workspace and project and dataset) else 0
        comp_b = 25 if sus_conf_data.get("process_fitness") is not None else 0
        comp_c = 25 if (esg_score and esg_score.overall_score is not None) else 0
        comp_d = 25 if len(recs_payload) > 0 else 0
        completeness_score = comp_a + comp_b + comp_c + comp_d

        # Audit Readiness Classification
        if completeness_score >= 95:
            readiness_class = "Audit Ready"
        elif completeness_score >= 80:
            readiness_class = "Near Audit Ready"
        elif completeness_score >= 60:
            readiness_class = "Partial Evidence"
        else:
            readiness_class = "Insufficient Evidence"

        # Example heuristic formula
        fitness_pct = sus_conf_data.get("process_fitness", 0.0) * 100
        emissions_val = carbon_fitness_data.get("actual_emissions_kg", 0.0)
        hotspots_count = len(hotspots)
        bottlenecks_count = len(bottlenecks)
        worst_bot_text = f"at '{max(bottlenecks, key=lambda x: x.average_wait_time).activity_name}'" if bottlenecks else "N/A"
        worst_hot_text = f"at '{max(hotspots, key=lambda x: x.emissions).activity_name}'" if hotspots else "N/A"
        budget_status_text = "exceeding budget limits" if budget_exceeded else "conforming to limits"
        
        narrative = (
            f"This BRSR Compliance Report (v{self.get_next_version(analysis_id)}) aggregates transaction-level proofs from workspace '{workspace.name if workspace else 'Unknown'}' "
            f"for project '{project.name if project else 'Unknown'}'. The report is generated from analysis run version {analysis.analysis_version} "
            f"representing period {esg_score.period if esg_score else '2026'}. The compliance check yields a fitness score of {fitness_pct:.1f}% "
            f"with {len(deviations)} deviations and {bottlenecks_count} bottleneck activity nodes, where the worst delay is {worst_bot_text}. "
            f"Carbon attribution models tracked a total actual emission of {emissions_val:,.1f} kg CO2e ({budget_status_text}), "
            f"identifying {hotspots_count} significant carbon hotspots with the largest hotspot {worst_hot_text}. "
            f"ESG overall scoring achieved {esg_val * 100:.1f}%, monitoring {len(suppliers_raw)} suppliers. "
            f"Based on the collected evidence, this disclosure has a completeness score of {completeness_score}% "
            f"and is classified as '{readiness_class}'."
        )

        # Generate payload version & IDs
        report_id = str(uuid.uuid4())
        report_version = self.get_next_version(analysis_id)

        # Build initial structured payload
        payload = {
            "report_id": report_id,
            "analysis_id": str(analysis_id),
            "workspace_id": str(analysis.workspace_id),
            "tenant_id": str(analysis.tenant_id),
            "generated_at": generated_at,
            "report_version": report_version,
            "status": "completed",
            "report_completeness_score": completeness_score,
            
            # Completeness Breakdown
            "report_completeness_breakdown": {
                "section_a": comp_a,
                "section_b": comp_b,
                "section_c": comp_c,
                "recommendations": comp_d
            },
            
            # Audit Readiness Classification
            "audit_readiness": readiness_class,
            
            # Executive Summary Narrative
            "executive_summary": narrative,

            # Export flags
            "export_ready": True,
            "report_type": "BRSR",
            "schema_version": "1.0",
            
            # Export metadata inside report payload
            "pdf_available": False,
            "docx_available": False,
            "pdf_path": None,
            "docx_path": None,
            "last_exported_at": None,

            # Integrity snapshot
            "generated_from_analysis_version": analysis.analysis_version,
            "generated_from_dataset_id": str(analysis.dataset_id),
            "generated_from_dataset_name": dataset.name if dataset else "Unknown Dataset",
            "generated_from_project_id": str(analysis.project_id),
            "snapshot_timestamp": generated_at,

            # Sections
            "section_a": section_a,
            "section_b": section_b,
            "section_c": section_c,
            "section_d": section_d,
            "recommendations": recs_payload
        }

        # Generate SHA256 Hash of the payload and store it inside
        payload_str = json.dumps(payload, sort_keys=True)
        sha256_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        payload["sha256_hash"] = sha256_hash

        # Write immutable snapshot file
        report_file = os.path.join(REPORTS_DIR, f"brsr_{report_id}.json")
        with open(report_file, "w") as f:
            json.dump(payload, f, indent=2)

        # Write latest pointer file
        latest_file = os.path.join(REPORTS_DIR, f"latest_brsr_{analysis_id}.json")
        with open(latest_file, "w") as f:
            json.dump({"report_id": report_id, "generated_at": generated_at}, f, indent=2)

        return payload

    def get_report(self, report_id: str) -> dict:
        report_file = os.path.join(REPORTS_DIR, f"brsr_{report_id}.json")
        if not os.path.exists(report_file):
            raise FileNotFoundError("Report not found")
        with open(report_file, "r") as f:
            return json.load(f)

    def save_report_payload(self, report_id: str, payload: dict) -> None:
        report_file = os.path.join(REPORTS_DIR, f"brsr_{report_id}.json")
        with open(report_file, "w") as f:
            json.dump(payload, f, indent=2)

    def get_latest_report(self, analysis_id: uuid.UUID) -> dict:
        latest_file = os.path.join(REPORTS_DIR, f"latest_brsr_{analysis_id}.json")
        if not os.path.exists(latest_file):
            raise FileNotFoundError("Latest report not found")
        with open(latest_file, "r") as f:
            latest_data = json.load(f)
            report_id = latest_data.get("report_id")
            return self.get_report(report_id)
