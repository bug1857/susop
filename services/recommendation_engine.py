import os
import uuid
import json
import hashlib
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from app.models.models import (
    AiRecommendation,
    RecommendationEvidence,
    ProcessAnalysis,
    Workspace,
    Project,
    Organization,
    Dataset,
    ConformanceResult,
    ConformanceDeviation,
    EmissionHotspot,
    ProcessBottleneck,
    EsgScore
)
from app.core.ingestion import detect_delimiter

class RecommendationEngine:
    def __init__(self, db: Session):
        self.db = db

    def generate_and_persist(self, analysis_id: uuid.UUID) -> List[Dict[str, Any]]:
        # 1. Fetch analysis and related models
        analysis = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == analysis_id,
            ProcessAnalysis.is_deleted == False
        ).first()
        if not analysis:
            raise ValueError("Analysis not found")

        workspace = self.db.query(Workspace).filter(Workspace.id == analysis.workspace_id).first()
        project = self.db.query(Project).filter(Project.id == analysis.project_id).first()
        dataset = self.db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()

        # 2. Get next version number using DB-level JSON extraction
        max_ver = self.db.query(
            func.max(func.json_extract(AiRecommendation.recommendation_metadata, '$.recommendation_version'))
        ).filter(
            AiRecommendation.analysis_id == analysis_id,
            AiRecommendation.is_deleted == False
        ).scalar()
        
        next_version = int(max_ver) + 1 if max_ver is not None else 1
        run_id = str(uuid.uuid4())
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 3. Gather data sources
        conf_result = self.db.query(ConformanceResult).filter(
            ConformanceResult.analysis_id == analysis_id
        ).first()

        deviations = self.db.query(ConformanceDeviation).filter(
            ConformanceDeviation.analysis_id == analysis_id
        ).all()

        hotspots = self.db.query(EmissionHotspot).filter(
            EmissionHotspot.analysis_id == analysis_id
        ).all()

        bottlenecks = self.db.query(ProcessBottleneck).filter(
            ProcessBottleneck.analysis_id == analysis_id,
            ProcessBottleneck.is_deleted == False
        ).all()

        esg_score = self.db.query(EsgScore).filter(
            EsgScore.workspace_id == analysis.workspace_id,
            EsgScore.is_deleted == False
        ).order_by(EsgScore.calculated_at.desc()).first()

        # Parse supplier metrics from CSV
        suppliers_raw = []
        if dataset and os.path.exists(dataset.original_file_path):
            try:
                delim = detect_delimiter(dataset.original_file_path)
                df = pd.read_csv(dataset.original_file_path, sep=delim)
                mappings = dataset.mappings or {}
                role_to_header = {role: header for header, role in mappings.items()}

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
                        supp_name = str(group[name_col].iloc[0]) if not group[name_col].empty else str(supp_id)
                        supp_country = str(group[country_c].iloc[0]) if (country_c and not group[country_c].empty) else "Unknown"
                        supp_emissions = float(pd.to_numeric(group[carb_c], errors="coerce").sum()) if carb_c else 0.0
                        supp_spend = float(pd.to_numeric(group[cost_c], errors="coerce").sum()) if cost_c else 0.0
                        supp_risk = str(group[risk_c].value_counts().index[0]) if (risk_c and not group[risk_c].empty) else "Low"

                        # Same esg calculation logic
                        score = 80
                        if supp_risk == "Critical":
                            score -= 30
                        elif supp_risk == "High":
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
            except Exception:
                pass

        # 4. Generate candidate recommendations list
        candidates = []

        # -- A. Carbon Reduction Recommendations --
        for hotspot in hotspots:
            if hotspot.contribution_percentage > 20.0:
                # Calculate estimated reductions
                reduction_factor = 0.15 if "Logistics" in hotspot.activity_name or "Freight" in hotspot.activity_name else 0.10
                est_carbon_red = hotspot.emissions * reduction_factor
                # Default metrics
                carbon_impact = min(100.0, hotspot.contribution_percentage * 2.0)
                compliance_impact = 40.0
                cost_impact = 50.0
                
                # Confidence score calculation (normalized 0-100)
                data_completeness = 35.0
                evidence_quality = 30.0 if hotspot.emissions > 10000 else 20.0
                source_reliability = 30.0
                confidence_score = data_completeness + evidence_quality + source_reliability

                priority_score = round(
                    0.35 * carbon_impact +
                    0.25 * compliance_impact +
                    0.20 * cost_impact +
                    0.20 * confidence_score
                )

                candidates.append({
                    "title": f"Reduce emissions from {hotspot.activity_name}",
                    "description": f"Activity contributes {hotspot.contribution_percentage:.1f}% of total carbon footprint. Consider alternative transport/processing methods.",
                    "category": "Carbon Reduction",
                    "db_type": "CARBON_HOTSPOT",
                    "estimated_carbon_reduction": est_carbon_red,
                    "estimated_cost_reduction": est_carbon_red * 0.05, # Cost savings estimate proportional to carbon
                    "estimated_compliance_improvement": 0.0,
                    "estimated_risk_reduction": 0.0,
                    "confidence_score": confidence_score,
                    "priority_score": priority_score,
                    "source_engine": "Carbon Attribution",
                    "source_table": "emission_hotspots",
                    "source_record_id": str(hotspot.id),
                    "generated_rule": "rule_hotspot_emissions_gt_20",
                    "evidence": [
                        {
                            "metric_name": "Carbon Footprint Contribution",
                            "metric_value": f"{hotspot.contribution_percentage:.1f}%",
                            "metric_threshold": "20.0%",
                            "source_engine": "Carbon Attribution",
                            "severity_contribution": 40
                        },
                        {
                            "metric_name": "Activity Absolute Emissions",
                            "metric_value": f"{hotspot.emissions:.1f} kg",
                            "metric_threshold": "10000.0 kg",
                            "source_engine": "Carbon Attribution",
                            "severity_contribution": 60
                        }
                    ],
                    "supporting_metrics": {
                        "activity_name": hotspot.activity_name,
                        "contribution_percentage": hotspot.contribution_percentage,
                        "emissions_kg": hotspot.emissions,
                        "reduction_factor": reduction_factor,
                        "methodology": "estimated_carbon_reduction = activity_emissions * reduction_factor"
                    }
                })

        # -- B. Conformance Recommendations --
        if conf_result and conf_result.fitness_score < 0.90:
            est_comp_imp = (1.0 - conf_result.fitness_score) * 100.0
            carbon_impact = 30.0
            compliance_impact = est_comp_imp
            cost_impact = 40.0
            
            data_completeness = 35.0
            evidence_quality = 35.0 if len(deviations) > 5 else 20.0
            source_reliability = 30.0
            confidence_score = data_completeness + evidence_quality + source_reliability

            priority_score = round(
                0.35 * carbon_impact +
                0.25 * compliance_impact +
                0.20 * cost_impact +
                0.20 * confidence_score
            )

            candidates.append({
                "title": "Resolve process conformance deviations",
                "description": f"Process fitness score is below threshold ({conf_result.fitness_score:.3f}). Total of {len(deviations)} deviations detected in execution traces.",
                "category": "Conformance",
                "db_type": "CONFORMANCE_RISK",
                "estimated_carbon_reduction": 0.0,
                "estimated_cost_reduction": len(deviations) * 150.0, # Cost savings estimate per deviation resolved
                "estimated_compliance_improvement": est_comp_imp,
                "estimated_risk_reduction": 0.0,
                "confidence_score": confidence_score,
                "priority_score": priority_score,
                "source_engine": "Conformance Checking",
                "source_table": "conformance_results",
                "source_record_id": str(conf_result.id),
                "generated_rule": "rule_fitness_lt_0_90",
                "evidence": [
                    {
                        "metric_name": "Process Fitness Score",
                        "metric_value": f"{conf_result.fitness_score:.3f}",
                        "metric_threshold": "0.900",
                        "source_engine": "Conformance Checking",
                        "severity_contribution": 50
                    },
                    {
                        "metric_name": "Deviations Count",
                        "metric_value": str(len(deviations)),
                        "metric_threshold": "5",
                        "source_engine": "Conformance Checking",
                        "severity_contribution": 50
                    }
                ],
                "supporting_metrics": {
                    "fitness_score": conf_result.fitness_score,
                    "deviations_count": len(deviations),
                    "methodology": "estimated_compliance_improvement = (1.0 - fitness_score) * 100"
                }
            })

        # -- C. Bottleneck Recommendations --
        for bot in bottlenecks:
            if bot.average_wait_time > 3600:
                # 3600 seconds = 1 hour
                carbon_impact = 20.0
                compliance_impact = 40.0
                cost_impact = min(100.0, bot.average_wait_time / 1000.0)
                
                data_completeness = 35.0
                evidence_quality = 30.0 if bot.occurrence_count > 10 else 20.0
                source_reliability = 30.0
                confidence_score = data_completeness + evidence_quality + source_reliability

                priority_score = round(
                    0.35 * carbon_impact +
                    0.25 * compliance_impact +
                    0.20 * cost_impact +
                    0.20 * confidence_score
                )

                candidates.append({
                    "title": f"Optimize bottleneck in {bot.activity_name}",
                    "description": f"Average wait time in activity is {bot.average_wait_time:.1f}s across {bot.occurrence_count} occurrences. This delay impacts overall lifecycle throughput.",
                    "category": "Bottleneck",
                    "db_type": "PROCESS_BOTTLENECK",
                    "estimated_carbon_reduction": 0.0,
                    "estimated_cost_reduction": bot.average_wait_time * 0.10,
                    "estimated_compliance_improvement": 0.0,
                    "estimated_risk_reduction": 0.0,
                    "confidence_score": confidence_score,
                    "priority_score": priority_score,
                    "source_engine": "Process Mining",
                    "source_table": "process_bottlenecks",
                    "source_record_id": str(bot.id),
                    "generated_rule": "rule_wait_time_gt_3600",
                    "evidence": [
                        {
                            "metric_name": "Average Wait Time",
                            "metric_value": f"{bot.average_wait_time:.1f}s",
                            "metric_threshold": "3600.0s",
                            "source_engine": "Process Mining",
                            "severity_contribution": 60
                        },
                        {
                            "metric_name": "Occurrence Count",
                            "metric_value": str(bot.occurrence_count),
                            "metric_threshold": "10",
                            "source_engine": "Process Mining",
                            "severity_contribution": 40
                        }
                    ],
                    "supporting_metrics": {
                        "activity_name": bot.activity_name,
                        "average_wait_time": bot.average_wait_time,
                        "occurrence_count": bot.occurrence_count,
                        "methodology": "throughput optimization recommendations prioritized based on wait times"
                    }
                })

        # -- D. ESG Recommendations --
        if esg_score and esg_score.overall_score < 0.90:
            carbon_impact = 35.0
            compliance_impact = 50.0
            cost_impact = 30.0
            
            data_completeness = 35.0
            evidence_quality = 30.0
            source_reliability = 30.0
            confidence_score = data_completeness + evidence_quality + source_reliability

            priority_score = round(
                0.35 * carbon_impact +
                0.25 * compliance_impact +
                0.20 * cost_impact +
                0.20 * confidence_score
            )

            candidates.append({
                "title": "Improve ESG overall score",
                "description": f"The calculated ESG overall score is {esg_score.overall_score:.3f}, below the target of 0.90. Address missing data and compliance disclosures.",
                "category": "ESG",
                "db_type": "ESG_RISK",
                "estimated_carbon_reduction": 0.0,
                "estimated_cost_reduction": 0.0,
                "estimated_compliance_improvement": 15.0,
                "estimated_risk_reduction": 0.0,
                "confidence_score": confidence_score,
                "priority_score": priority_score,
                "source_engine": "ESG Scoring Engine",
                "source_table": "esg_scores",
                "source_record_id": str(esg_score.id),
                "generated_rule": "rule_esg_overall_lt_0_90",
                "evidence": [
                    {
                        "metric_name": "ESG Overall Score",
                        "metric_value": f"{esg_score.overall_score:.3f}",
                        "metric_threshold": "0.900",
                        "source_engine": "ESG Scoring Engine",
                        "severity_contribution": 100
                    }
                ],
                "supporting_metrics": {
                    "esg_overall_score": esg_score.overall_score,
                    "environmental_score": esg_score.environmental_score,
                    "social_score": esg_score.social_score,
                    "governance_score": esg_score.governance_score,
                    "methodology": "overall score gap analysis"
                }
            })

        # -- E. Supplier Recommendations --
        for supp in suppliers_raw:
            if supp["esg_score"] < 0.70:
                # Estimated risk reduction
                weighting = 50.0
                est_risk_red = supp["esg_score"] * weighting
                
                carbon_impact = 40.0
                compliance_impact = 40.0
                cost_impact = 40.0
                
                data_completeness = 35.0
                evidence_quality = 20.0
                source_reliability = 30.0
                confidence_score = data_completeness + evidence_quality + source_reliability

                priority_score = round(
                    0.35 * carbon_impact +
                    0.25 * compliance_impact +
                    0.20 * cost_impact +
                    0.20 * confidence_score
                )

                candidates.append({
                    "title": f"Remediate supplier risk: {supp['supplier_name']}",
                    "description": f"Supplier ESG rating is below target ({supp['esg_score']:.2f}) and presents a {supp['risk_level']} risk level. Focus on emissions reduction and sourcing audit.",
                    "category": "Supplier",
                    "db_type": "ESG_RISK",
                    "estimated_carbon_reduction": supp["emissions"] * 0.10,
                    "estimated_cost_reduction": 0.0,
                    "estimated_compliance_improvement": 0.0,
                    "estimated_risk_reduction": est_risk_red,
                    "confidence_score": confidence_score,
                    "priority_score": priority_score,
                    "source_engine": "Supplier Intelligence",
                    "source_table": "supplier_metrics",
                    "source_record_id": str(supp["supplier_id"]),
                    "generated_rule": "rule_supplier_esg_lt_0_70",
                    "evidence": [
                        {
                            "metric_name": "Supplier ESG Score",
                            "metric_value": f"{supp['esg_score']:.2f}",
                            "metric_threshold": "0.70",
                            "source_engine": "Supplier Intelligence",
                            "severity_contribution": 60
                        },
                        {
                            "metric_name": "Supplier Risk Level",
                            "metric_value": supp["risk_level"],
                            "metric_threshold": "Low",
                            "source_engine": "Supplier Intelligence",
                            "severity_contribution": 40
                        }
                    ],
                    "supporting_metrics": {
                        "supplier_id": supp["supplier_id"],
                        "supplier_name": supp["supplier_name"],
                        "esg_score": supp["esg_score"],
                        "risk_level": supp["risk_level"],
                        "methodology": "estimated_risk_reduction = supplier_risk_score * weighting"
                    }
                })

        # -- F. Compliance Risk Recommendations --
        # Add Compliance Risk if carbon budget is exceeded
        if conf_result and conf_result.budget_exceeded:
            carbon_impact = 50.0
            compliance_impact = 80.0
            cost_impact = 30.0
            
            data_completeness = 35.0
            evidence_quality = 30.0
            source_reliability = 30.0
            confidence_score = data_completeness + evidence_quality + source_reliability

            priority_score = round(
                0.35 * carbon_impact +
                0.25 * compliance_impact +
                0.20 * cost_impact +
                0.20 * confidence_score
            )

            candidates.append({
                "title": "Mitigate Carbon Budget compliance violation",
                "description": f"The project carbon emissions ({conf_result.actual_emissions:.1f} kg) have exceeded the reference budget ({conf_result.carbon_budget:.1f} kg). Compliance improvement actions required immediately.",
                "category": "Compliance Risk",
                "db_type": "CONFORMANCE_RISK",
                "estimated_carbon_reduction": conf_result.actual_emissions - conf_result.carbon_budget,
                "estimated_cost_reduction": 0.0,
                "estimated_compliance_improvement": 20.0,
                "estimated_risk_reduction": 0.0,
                "confidence_score": confidence_score,
                "priority_score": priority_score,
                "source_engine": "Conformance Checking",
                "source_table": "conformance_results",
                "source_record_id": str(conf_result.id),
                "generated_rule": "rule_carbon_budget_exceeded",
                "evidence": [
                    {
                        "metric_name": "Actual Emissions vs Budget",
                        "metric_value": f"{conf_result.actual_emissions:.1f} / {conf_result.carbon_budget:.1f} kg",
                        "metric_threshold": "Carbon Budget limit exceeded",
                        "source_engine": "Conformance Checking",
                        "severity_contribution": 100
                    }
                ],
                "supporting_metrics": {
                    "actual_emissions": conf_result.actual_emissions,
                    "carbon_budget": conf_result.carbon_budget,
                    "budget_exceeded": conf_result.budget_exceeded,
                    "methodology": "carbon compliance violation tracking"
                }
            })

        # -- G. Data Quality Recommendations --
        if not dataset or not dataset.mappings:
            carbon_impact = 10.0
            compliance_impact = 30.0
            cost_impact = 20.0
            
            data_completeness = 10.0
            evidence_quality = 20.0
            source_reliability = 30.0
            confidence_score = data_completeness + evidence_quality + source_reliability

            priority_score = round(
                0.35 * carbon_impact +
                0.25 * compliance_impact +
                0.20 * cost_impact +
                0.20 * confidence_score
            )

            candidates.append({
                "title": "Configure dataset column mappings",
                "description": "Incomplete column mappings prevent automatic extraction of ESG metrics, carbon intensities, and process wait times.",
                "category": "Data Quality",
                "db_type": "DATA_QUALITY",
                "estimated_carbon_reduction": 0.0,
                "estimated_cost_reduction": 0.0,
                "estimated_compliance_improvement": 5.0,
                "estimated_risk_reduction": 0.0,
                "confidence_score": confidence_score,
                "priority_score": priority_score,
                "source_engine": "Ingestion Pipeline",
                "source_record_id": str(analysis_id),
                "source_table": "datasets",
                "generated_rule": "rule_missing_mappings",
                "evidence": [
                    {
                        "metric_name": "Mappings Configured",
                        "metric_value": "0",
                        "metric_threshold": "1",
                        "source_engine": "Ingestion Pipeline",
                        "severity_contribution": 100
                    }
                ],
                "supporting_metrics": {
                    "methodology": "mapping coverage check"
                }
            })

        # Apply ranking by sorting priority_score descending
        candidates.sort(key=lambda x: x["priority_score"], reverse=True)

        # 5. Persist to DB and return
        db_records = []
        for cand in candidates:
            # Stage 1 - Base Severity
            p_score = cand["priority_score"]
            if p_score >= 95:
                severity = "Critical"
            elif p_score >= 80:
                severity = "High"
            elif p_score >= 60:
                severity = "Medium"
            else:
                severity = "Low"

            def elevate_one_level(sev: str) -> str:
                if sev == "Low": return "Medium"
                if sev == "Medium": return "High"
                if sev in ["High", "Critical"]: return "Critical"
                return sev

            # Stage 2 - Controlled Elevation
            if conf_result and conf_result.budget_exceeded:
                severity = elevate_one_level(severity)
            if conf_result and conf_result.fitness_score < 0.85:
                severity = elevate_one_level(severity)
            if cand["category"] == "Carbon Reduction":
                contrib = cand["supporting_metrics"].get("contribution_percentage", 0.0)
                if contrib > 30.0:
                    severity = elevate_one_level(severity)
            if cand["category"] == "Supplier":
                supp_risk = cand["supporting_metrics"].get("risk_level", "Low")
                supp_esg = cand["supporting_metrics"].get("esg_score", 1.0)
                if supp_risk == "Critical" and supp_esg < 0.50:
                    severity = elevate_one_level(severity)

            metadata_payload = {
                "recommendation_run_id": run_id,
                "recommendation_version": next_version,
                "generated_at": generated_at,
                "category": cand["category"],
                "evidence": cand["evidence"],
                "supporting_metrics": cand["supporting_metrics"],
                "estimated_compliance_improvement": cand["estimated_compliance_improvement"],
                "estimated_risk_reduction": cand["estimated_risk_reduction"],
                "source_engine": cand["source_engine"],
                "source_table": cand["source_table"],
                "source_record_id": cand["source_record_id"],
                "generated_rule": cand["generated_rule"],
                "export_ready": True,
                "schema_version": "1.0",
                "priority_score": p_score,
                "confidence_score": cand["confidence_score"],
                
                # Green Rerouting compatibility contract
                "candidate_activity": None,
                "candidate_action": None,

                # Lineage metadata
                "generated_from_analysis_version": analysis.analysis_version,
                "generated_from_dataset_id": str(analysis.dataset_id),
                "generated_from_project_id": str(analysis.project_id),
                "generated_from_conformance_result_id": str(conf_result.id) if conf_result else None,
                "generated_from_esg_score_id": str(esg_score.id) if esg_score else None
            }

            # Calculate SHA256 snapshot hash of metadata JSON string for validation check
            payload_str = json.dumps(metadata_payload, sort_keys=True)
            snapshot_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
            metadata_payload["snapshot_hash"] = snapshot_hash
            metadata_payload["snapshot_timestamp"] = generated_at

            db_rec = AiRecommendation(
                tenant_id=analysis.tenant_id,
                workspace_id=analysis.workspace_id,
                project_id=analysis.project_id,
                analysis_id=analysis_id,
                recommendation_type=cand["db_type"],
                title=cand["title"],
                description=cand["description"],
                estimated_emission_reduction=cand["estimated_carbon_reduction"],
                estimated_cost_reduction=cand["estimated_cost_reduction"],
                priority=severity.upper(),
                status="ACTIVE",
                recommendation_confidence_score=cand["confidence_score"],
                recommendation_metadata=metadata_payload
            )

            self.db.add(db_rec)
            db_records.append(db_rec)

        self.db.commit()

        return self._map_to_output(db_records)

    def get_latest_recommendations(self, analysis_id: uuid.UUID) -> List[Dict[str, Any]]:
        # Find highest version number
        max_ver = self.db.query(
            func.max(func.json_extract(AiRecommendation.recommendation_metadata, '$.recommendation_version'))
        ).filter(
            AiRecommendation.analysis_id == analysis_id,
            AiRecommendation.is_deleted == False
        ).scalar()

        if max_ver is None:
            # Auto-generate V1 on first fetch if none exist
            return self.generate_and_persist(analysis_id)

        # Retrieve records matching this specific version using fast JSON extraction query
        records = self.db.query(AiRecommendation).filter(
            AiRecommendation.analysis_id == analysis_id,
            AiRecommendation.is_deleted == False,
            func.json_extract(AiRecommendation.recommendation_metadata, '$.recommendation_version') == max_ver
        ).all()

        return self._map_to_output(records)

    def get_version_recommendations(self, analysis_id: uuid.UUID, version: int) -> List[Dict[str, Any]]:
        # Retrieve records matching this specific version using fast JSON extraction query
        records = self.db.query(AiRecommendation).filter(
            AiRecommendation.analysis_id == analysis_id,
            AiRecommendation.is_deleted == False,
            func.json_extract(AiRecommendation.recommendation_metadata, '$.recommendation_version') == version
        ).all()

        if not records:
            raise FileNotFoundError(f"Version {version} not found")

        return self._map_to_output(records)

    def get_history(self, analysis_id: uuid.UUID) -> List[Dict[str, Any]]:
        # Retrieve all non-deleted recommendations for this analysis
        records = self.db.query(AiRecommendation).filter(
            AiRecommendation.analysis_id == analysis_id,
            AiRecommendation.is_deleted == False
        ).all()

        # Group by run_id/version
        batches = {}
        for r in records:
            meta = r.recommendation_metadata or {}
            run_id = meta.get("recommendation_run_id")
            ver = meta.get("recommendation_version")
            gen_at = meta.get("generated_at")
            if not run_id or ver is None:
                continue

            if run_id not in batches:
                batches[run_id] = {
                    "recommendation_run_id": run_id,
                    "recommendation_version": ver,
                    "generated_at": gen_at,
                    "recommendation_count": 0,
                    "critical_count": 0,
                    "total_estimated_carbon_reduction": 0.0
                }

            batches[run_id]["recommendation_count"] += 1
            if r.priority.upper() == "CRITICAL":
                batches[run_id]["critical_count"] += 1
            batches[run_id]["total_estimated_carbon_reduction"] += r.estimated_emission_reduction

        history = list(batches.values())
        # Ordered by recommendation_version ascending
        history.sort(key=lambda x: x["recommendation_version"])
        return history

    def _map_to_output(self, db_records: List[AiRecommendation]) -> List[Dict[str, Any]]:
        # Sort priority_score descending
        def get_priority_score(r):
            meta = r.recommendation_metadata or {}
            return meta.get("priority_score", 0)
        records_sorted = sorted(db_records, key=get_priority_score, reverse=True)

        out_list = []
        for r in records_sorted:
            meta = r.recommendation_metadata or {}
            out_list.append({
                "recommendation_id": str(r.id),
                "title": r.title,
                "description": r.description,
                "category": meta.get("category", r.recommendation_type),
                "severity": r.priority.capitalize(),
                "priority_score": meta.get("priority_score", 0),
                "confidence_score": r.recommendation_confidence_score,
                "estimated_carbon_reduction": r.estimated_emission_reduction,
                "estimated_cost_reduction": r.estimated_cost_reduction,
                "estimated_compliance_improvement": meta.get("estimated_compliance_improvement", 0.0),
                "source_engine": meta.get("source_engine", ""),
                "evidence": meta.get("evidence", []),
                "supporting_metrics": meta.get("supporting_metrics", {}),
                
                # Green Rerouting compatibility contract fields
                "candidate_activity": meta.get("candidate_activity"),
                "candidate_action": meta.get("candidate_action"),

                # Lineage metadata
                "generated_from_analysis_version": meta.get("generated_from_analysis_version"),
                "generated_from_dataset_id": meta.get("generated_from_dataset_id"),
                "generated_from_project_id": meta.get("generated_from_project_id"),
                "generated_from_conformance_result_id": meta.get("generated_from_conformance_result_id"),
                "generated_from_esg_score_id": meta.get("generated_from_esg_score_id"),

                # Snapshots validation keys
                "snapshot_hash": meta.get("snapshot_hash"),
                "snapshot_timestamp": meta.get("snapshot_timestamp")
            })
        return out_list
