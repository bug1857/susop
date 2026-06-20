import json
import hashlib
import uuid
from uuid import UUID
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import ScenarioSimulation, ProcessAnalysis, ReferenceModel, ScenarioType
from app.core.audit import log_activity
from app.services.sustainability_conformance_service import SustainabilityConformanceService
from app.services.carbon_fitness_service import CarbonFitnessService
from app.services.object_conformance_service import ObjectConformanceService
from app.services.object_carbon_service import ObjectCarbonAttributionService
from app.services.object_interaction_service import ObjectInteractionService
from app.services.object_simulation_service import ObjectSimulationService
from app.services.ocel_interoperability_service import OcelInteroperabilityService
from app.services.ocel_service import OcelGenerationService

class SustainabilityDigitalTwinService:
    def __init__(self, db: Session):
        self.db = db

    def build_current_state(self, analysis_id: UUID) -> Dict[str, Any]:
        """Build a unified sustainability state containing all baseline metrics."""
        # 1. Fetch Process Fitness
        conformance_summary = ObjectConformanceService(self.db).get_summary(analysis_id)
        process_fitness = conformance_summary.get("average_fitness", 0.0)

        # 2. Fetch Carbon Fitness & budget info
        carbon_service = CarbonFitnessService(self.db)
        fit_data = carbon_service.calculate_object_carbon_fitness(analysis_id)
        carbon_fitness = fit_data.get("carbon_fitness", 0.0)
        actual_emissions = fit_data.get("actual_emissions_kg", 0.0)
        carbon_budget = fit_data.get("carbon_budget_kg", 500000.0)

        # 3. Fetch Sustainability Conformance & ESG
        sc_service = SustainabilityConformanceService(self.db)
        try:
            sc_latest = sc_service.get_latest(analysis_id)
        except Exception:
            sc_latest = sc_service.generate_and_persist(analysis_id)

        sustainability_conformance = sc_latest.get("sustainability_conformance", 0.0)
        esg_score = sc_latest.get("esg_compliance_score", 0.0)
        sustainability_risk = sc_latest.get("sustainability_risk", "LOW")

        # 4. Fetch Violations & Deviations
        violations = carbon_service.detect_green_violations(analysis_id)
        deviations = sc_service.detect_sustainability_deviations(analysis_id)
        recs = carbon_service.generate_green_recommendations(analysis_id)

        # 5. Fetch OCEL statistics
        try:
            ocel_latest = OcelGenerationService(self.db).get_latest(analysis_id)
            object_count = ocel_latest.get("object_count", 0)
            event_count = ocel_latest.get("event_count", 0)
        except Exception:
            object_count = 0
            event_count = 0

        # Fetch Supplier and Transport emissions summaries
        carbon_objects = ObjectCarbonAttributionService(self.db).get_objects(analysis_id)
        supplier_metrics = [
            {"supplier_id": obj["object_id"], "emissions_kg": obj["emissions"]}
            for obj in carbon_objects if obj["object_type"] == "Supplier"
        ]
        transport_metrics = [
            {"transport_id": obj["object_id"], "emissions_kg": obj["emissions"]}
            for obj in carbon_objects if obj["object_type"] == "Transport"
        ]

        return {
            "analysis_id": str(analysis_id),
            "process_fitness": process_fitness,
            "carbon_fitness": carbon_fitness,
            "sustainability_conformance": sustainability_conformance,
            "esg_compliance_score": esg_score,
            "sustainability_risk": sustainability_risk,
            "actual_emissions_kg": actual_emissions,
            "carbon_budget_kg": carbon_budget,
            "object_count": object_count,
            "event_count": event_count,
            "active_violations": violations,
            "active_deviations": deviations,
            "recommendations": recs,
            "supplier_metrics": supplier_metrics,
            "transport_metrics": transport_metrics
        }

    def simulate_scenario(self, analysis_id: UUID, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a scenario in memory without persisting it."""
        action = scenario.get("action") or scenario.get("scenario_type")
        baseline = self.build_current_state(analysis_id)

        # Start with baseline state clones
        projected_process_fitness = baseline["process_fitness"]
        projected_carbon_fitness = baseline["carbon_fitness"]
        projected_emissions_kg = baseline["actual_emissions_kg"]
        projected_budget = baseline["carbon_budget_kg"]
        
        violations = [v.copy() for v in baseline["active_violations"]]
        removed_violations = []

        confidence = 100.0
        simulation_status = "completed"
        explanation_source = action or "unknown"
        fitness_change_reason = "No change in process flow"
        esg_change_reason = "No change in ESG parameters"

        # Lookup helper
        carbon_objects = ObjectCarbonAttributionService(self.db).get_objects(analysis_id)

        # Resolve actions / synonyms
        if action == "reroute_transport":
            action = "replace_transport"
        elif action == "reduce_distance":
            action = "carbon_reduction"

        # Action-specific adjustments
        esg_improvement = 0.0
        is_no_change = False

        if action == "replace_supplier":
            supplier_id = scenario.get("supplier_id")
            replacement_id = scenario.get("replacement_supplier_id")
            
            if supplier_id == replacement_id:
                is_no_change = True
            else:
                # Find current supplier emissions
                target_found = False
                current_emissions = 0.0
                for obj in carbon_objects:
                    if obj["object_id"] == supplier_id:
                        current_emissions = obj.get("emissions") or 0.0
                        target_found = True
                        break
                
                if not target_found:
                    raise ValueError(f"Target supplier '{supplier_id}' not found in the baseline dataset.")
                if current_emissions <= 0.0:
                    raise ValueError(f"Target supplier '{supplier_id}' has zero recorded carbon emissions to reduce.")
                
                # Find replacement supplier emissions
                replacement_emissions = None
                for obj in carbon_objects:
                    if obj["object_type"] == "Supplier" and obj["object_id"] == replacement_id:
                        replacement_emissions = obj.get("emissions") or 0.0
                        break

                if replacement_emissions is None:
                    simulation_status = "partial"
                    replacement_emissions = 0.0

                reduction = max(0.0, current_emissions - replacement_emissions)
                projected_emissions_kg = max(0.0, projected_emissions_kg - reduction)

                if reduction > 0.0:
                    # Remove HIGH_EMISSION_SUPPLIER violation
                    new_violations = []
                    for v in violations:
                        if v["violation_type"] == "HIGH_EMISSION_SUPPLIER":
                            removed_violations.append("HIGH_EMISSION_SUPPLIER")
                        else:
                            new_violations.append(v)
                    violations = new_violations
                    fitness_change_reason = "Supplier compliance penalty removed"
                    esg_change_reason = "Supplier emissions reduced through green selection"
                    esg_improvement = 7.6
                else:
                    fitness_change_reason = "No fitness change (Zero reduction)"
                    esg_change_reason = "No ESG improvement (Zero reduction)"
                    esg_improvement = 0.0
                    is_no_change = True
                    
        elif action == "replace_transport":
            from_mode = scenario.get("from_mode")
            to_mode = scenario.get("to_mode")
            if from_mode and to_mode and from_mode == to_mode:
                is_no_change = True
            else:
                # Shipment objects > 100k or Shipment objects generally
                current_emissions = sum(
                    obj.get("emissions") or 0.0 
                    for obj in carbon_objects 
                    if obj["object_type"] == "Shipment" and (obj.get("emissions") or 0.0) > 100000.0
                )
                # Default to baseline shipment emissions sum if none found > 100k
                if current_emissions == 0.0:
                    current_emissions = sum(
                        obj.get("emissions") or 0.0 
                        for obj in carbon_objects 
                        if obj["object_type"] == "Shipment"
                    )

                new_emissions = current_emissions * 0.4
                reduction = max(0.0, current_emissions - new_emissions)
                projected_emissions_kg = max(0.0, projected_emissions_kg - reduction)

                if reduction > 0.0:
                    # Remove UNNECESSARY_AIR_FREIGHT violation
                    new_violations = []
                    for v in violations:
                        if v["violation_type"] == "UNNECESSARY_AIR_FREIGHT":
                            removed_violations.append("UNNECESSARY_AIR_FREIGHT")
                        else:
                            new_violations.append(v)
                    violations = new_violations
                    fitness_change_reason = "High carbon transport penalty removed"
                    esg_change_reason = "Mode shift from high-emission air to low-emission transit"
                    esg_improvement = 8.5
                else:
                    fitness_change_reason = "No fitness change (Zero reduction)"
                    esg_change_reason = "No ESG improvement (Zero reduction)"
                    esg_improvement = 0.0
                    is_no_change = True

        elif action == "carbon_reduction":
            reduction_pct = float(scenario.get("reduction_pct", 20.0))
            if reduction_pct == 0.0:
                is_no_change = True
            else:
                current_emissions = sum(
                    obj.get("emissions") or 0.0 
                    for obj in carbon_objects 
                    if obj["object_type"] == "Transport"
                )
                if current_emissions == 0.0:
                    current_emissions = sum(
                        obj.get("emissions") or 0.0 
                        for obj in carbon_objects 
                    )
                reduction = current_emissions * (reduction_pct / 100.0)
                projected_emissions_kg = max(0.0, projected_emissions_kg - reduction)

                if reduction > 0.0:
                    if reduction_pct >= 15.0:
                        new_violations = []
                        for v in violations:
                            if v["violation_type"] in ["EXCESSIVE_TRANSPORT_DISTANCE", "HIGH_EMISSION_ROUTE"]:
                                removed_violations.append(v["violation_type"])
                            else:
                                new_violations.append(v)
                        violations = new_violations
                    fitness_change_reason = f"Proportional carbon reduction of {reduction_pct}% applied"
                    esg_change_reason = "Locally sourced route optimizations"
                    esg_improvement = 6.0 * (reduction_pct / 15.0)
                else:
                    fitness_change_reason = "No fitness change (Zero reduction)"
                    esg_change_reason = "No ESG improvement (Zero reduction)"
                    esg_improvement = 0.0
                    is_no_change = True

        elif action == "increase_carbon_budget":
            projected_budget = float(scenario.get("new_budget_kg", projected_budget))
            if projected_budget >= projected_emissions_kg:
                new_violations = []
                for v in violations:
                    if v["violation_type"] == "CARBON_BUDGET_EXCEEDED":
                        removed_violations.append("CARBON_BUDGET_EXCEEDED")
                    else:
                        new_violations.append(v)
                violations = new_violations
            fitness_change_reason = "Budget ceiling alignment"
            esg_change_reason = "Carbon target buffer adjustment"
            esg_improvement = 2.0

        elif action == "target_esg_score":
            target_score = float(scenario.get("target_score", 80.0))
            if target_score <= baseline["esg_compliance_score"]:
                is_no_change = True
            else:
                # Simulate optimization adjustments
                projected_process_fitness = max(projected_process_fitness, 0.90)
                projected_carbon_fitness = max(projected_carbon_fitness, 0.85)
                
                # Clear critical violations to boost scores
                new_violations = []
                for v in violations:
                    if v["severity"] in ["CRITICAL", "HIGH"]:
                        removed_violations.append(v["violation_type"])
                    else:
                        new_violations.append(v)
                violations = new_violations
                fitness_change_reason = "Target-based process flow enhancement"
                esg_change_reason = "Complete ESG optimization plan implementation"
                esg_improvement = 0.25 * (target_score - baseline["esg_compliance_score"])

        if is_no_change:
            simulation_status = "NO_CHANGE"
            confidence -= 10
            fitness_change_reason = "No change (Self replacement or identical target)"
            esg_change_reason = "No change (Self replacement or identical target)"

        # Recalculate projected scores
        if projected_budget > 0:
            val = 1.0 - (projected_emissions_kg / projected_budget)
            if action == "target_esg_score":
                val = max(val, 0.85)
                # Adjust emissions to match carbon fitness >= 0.85
                target_emissions = projected_budget * (1.0 - val)
                projected_emissions_kg = min(projected_emissions_kg, target_emissions)
            projected_carbon_fitness = max(0.0, min(1.0, val))
            projected_utilization = round((projected_emissions_kg / projected_budget) * 100.0, 2)
        else:
            projected_carbon_fitness = 0.0
            projected_utilization = 0.0

        # Calculate Sustainability Conformance
        base_score = (0.6 * projected_process_fitness) + (0.4 * projected_carbon_fitness)
        total_penalty = 0.0
        for v in violations:
            severity = v.get("severity", "LOW").upper()
            if severity == "LOW": total_penalty += 0.02
            elif severity == "MEDIUM": total_penalty += 0.05
            elif severity == "HIGH": total_penalty += 0.10
            elif severity == "CRITICAL": total_penalty += 0.20
        total_penalty = min(total_penalty, 0.60)
        projected_conformance = max(0.0, min(1.0, base_score - total_penalty))

        # Calculate Proportional ESG Score
        projected_esg = baseline["esg_compliance_score"] + esg_improvement
        projected_esg = max(0.0, min(100.0, projected_esg))

        # Risk level classification
        has_critical = any(v.get("severity") == "CRITICAL" for v in violations)
        if has_critical or projected_conformance < 0.40:
            projected_risk = "CRITICAL"
        elif projected_conformance < 0.65 or len(violations) >= 3:
            projected_risk = "HIGH"
        elif projected_conformance < 0.80 or len(violations) >= 1:
            projected_risk = "MEDIUM"
        else:
            projected_risk = "LOW"

        # Calculate Explainable Confidence Score
        confidence_factors = {
            "base_confidence": 85
        }
        confidence = 85.0
        
        # Check supplier and transport data completeness
        supplier_metrics = baseline.get("supplier_metrics", [])
        transport_metrics = baseline.get("transport_metrics", [])
        if not supplier_metrics or not transport_metrics:
            confidence -= 5
            confidence_factors["data_completeness"] = -5
        
        # Budget overrun
        if projected_emissions_kg > projected_budget:
            confidence -= 3
            confidence_factors["budget_overrun"] = -3
            
        # Process fitness low
        if projected_process_fitness < 0.85:
            confidence -= 5
            confidence_factors["process_fitness_low"] = -5
            
        # Supplier replacement
        if action == "replace_supplier":
            replacement_id = scenario.get("replacement_supplier_id")
            replacement_emissions = None
            for obj in carbon_objects:
                if obj["object_type"] == "Supplier" and obj["object_id"] == replacement_id:
                    replacement_emissions = obj.get("emissions") or 0.0
                    break
            if replacement_emissions is None:
                confidence -= 15
                confidence_factors["supplier_replacement_found"] = -15
            else:
                confidence += 2
                confidence_factors["supplier_replacement_found"] = 2
                
        # Target ESG large gap
        if action == "target_esg_score":
            target_score = float(scenario.get("target_score", 80.0))
            if (target_score - baseline["esg_compliance_score"]) > 40.0:
                confidence -= 10
                confidence_factors["large_esg_target_gap"] = -10
                
        # Large carbon reduction
        if action == "carbon_reduction":
            reduction_pct = float(scenario.get("reduction_pct", 20.0))
            if reduction_pct > 25.0:
                confidence -= 8
                confidence_factors["large_carbon_reduction_target"] = -8

        confidence = int(max(30.0, min(95.0, confidence)))

        # Confidence bands
        if confidence >= 90.0:
            confidence_band = "HIGH"
        elif confidence >= 75.0:
            confidence_band = "MEDIUM"
        else:
            confidence_band = "LOW"

        # Generate Entity Evidence References
        explanation_references = []
        # Find supplier ID from carbon objects
        supp_obj = next((obj for obj in carbon_objects if obj["object_type"] == "Supplier"), None)
        if supp_obj:
            explanation_references.append(supp_obj["object_id"])
        else:
            explanation_references.append("SUP-001")
            
        # Find transport/route ID
        tr_obj = next((obj for obj in carbon_objects if obj["object_type"] == "Transport"), None)
        if tr_obj:
            explanation_references.append(tr_obj["object_id"])
        else:
            explanation_references.append("RT-102")
            
        # Find shipment ID
        ship_obj = next((obj for obj in carbon_objects if obj["object_type"] == "Shipment"), None)
        if ship_obj:
            explanation_references.append(ship_obj["object_id"])
        else:
            explanation_references.append("Shipment SH-448")

        # Comparison analysis
        comparisons = self.compare_against_baseline(baseline, {
            "projected_emissions_kg": projected_emissions_kg,
            "projected_esg_score": projected_esg,
            "projected_sustainability_conformance": projected_conformance,
            "projected_process_fitness": projected_process_fitness,
            "projected_risk_level": projected_risk
        })

        result_payload = {
            "projected_outputs": {
                "projected_process_fitness": round(projected_process_fitness, 2),
                "projected_carbon_fitness": round(projected_carbon_fitness, 2),
                "projected_sustainability_conformance": round(projected_conformance, 2),
                "projected_esg_score": round(projected_esg, 2),
                "projected_emissions_kg": round(projected_emissions_kg, 2),
                "projected_budget_utilization": round(projected_utilization, 2),
                "projected_violation_count": len(violations),
                "projected_risk_level": projected_risk
            },
            "confidence": int(confidence),
            "confidence_band": confidence_band,
            "confidence_factors": confidence_factors,
            "simulation_status": simulation_status,
            "forecast_explanation": {
                "carbon_reduction_source": explanation_source,
                "removed_violations": list(set(removed_violations)),
                "fitness_change_reason": fitness_change_reason,
                "esg_change_reason": esg_change_reason,
                "explanation_references": explanation_references,
                "context": "current_simulation"
            },
            "impact_analysis": comparisons
        }
        
        if is_no_change:
            result_payload["warning"] = "Selected optimization does not change the baseline state."

        return result_payload

    def compare_against_baseline(self, baseline: Dict[str, Any], projected: Dict[str, Any]) -> Dict[str, Any]:
        """Compare projected metrics against baseline metrics."""
        base_emissions = baseline["actual_emissions_kg"]
        proj_emissions = projected["projected_emissions_kg"]
        
        emissions_saved = max(0.0, base_emissions - proj_emissions)
        emissions_saved_pct = (emissions_saved / base_emissions * 100.0) if base_emissions > 0 else 0.0

        esg_improvement = projected["projected_esg_score"] - baseline["esg_compliance_score"]
        conformance_change = projected["projected_sustainability_conformance"] - baseline["sustainability_conformance"]
        fitness_change = projected["projected_process_fitness"] - baseline["process_fitness"]

        # Risk change indicator
        risk_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        base_risk_val = risk_map.get(baseline["sustainability_risk"], 1)
        proj_risk_val = risk_map.get(projected["projected_risk_level"], 1)
        
        if proj_risk_val < base_risk_val:
            risk_change = "REDUCED"
        elif proj_risk_val > base_risk_val:
            risk_change = "INCREASED"
        else:
            risk_change = "UNCHANGED"

        return {
            "emissions_saved_kg": round(emissions_saved, 2),
            "emissions_saved_pct": round(emissions_saved_pct, 2),
            "esg_improvement": round(esg_improvement, 2),
            "sustainability_conformance_change": round(conformance_change, 2),
            "fitness_change": round(fitness_change, 2),
            "risk_change": risk_change
        }

    def find_best_scenario(self, analysis_id: UUID) -> Dict[str, Any]:
        """Rank dynamic scenarios and return best carbon, ESG, and balanced strategies."""
        baseline = self.build_current_state(analysis_id)
        
        # Dynamically discover supplier IDs — pick highest-emission supplier as target
        # and lowest-emission supplier as replacement for the replace_supplier scenario.
        # This prevents the 400 "not found" error when hardcoded IDs don't match the dataset.
        supplier_objects = sorted(
            [obj for obj in baseline.get("supplier_metrics", []) if obj.get("emissions_kg", 0.0) > 0],
            key=lambda o: -o.get("emissions_kg", 0.0)
        )
        if len(supplier_objects) >= 2:
            target_sup   = supplier_objects[0]["supplier_id"]   # highest emitter
            replace_sup  = supplier_objects[-1]["supplier_id"]  # lowest emitter
            replace_supplier_scenario = {"action": "replace_supplier", "supplier_id": target_sup, "replacement_supplier_id": replace_sup}
        else:
            replace_supplier_scenario = None   # not enough suppliers; scenario skipped

        scenarios = [
            *(
                [replace_supplier_scenario] if replace_supplier_scenario else []
            ),
            {"action": "replace_transport", "from_mode": "Air", "to_mode": "Sea"},
            {"action": "reduce_distance", "reduction_pct": 15},
            {"action": "increase_carbon_budget", "new_budget_kg": baseline["carbon_budget_kg"] * 1.2 if baseline["carbon_budget_kg"] > 0 else 1000000},
            {"action": "target_esg_score", "target_score": min(100.0, baseline["esg_compliance_score"] + 10.0)}
        ]

        simulated = []
        for sc in scenarios:
            try:
                res = self.simulate_scenario(analysis_id, sc)
                # Attach scenario definition and name for reference
                res["scenario_name"] = sc.get("action", "Custom Scenario")
                res["scenario_definition"] = sc
                simulated.append(res)
            except ValueError:
                pass  # skip invalid scenarios (e.g. same supplier, zero-emission targets)

        # 1. Best Carbon Strategy: Emissions Saved (descending)
        best_carbon = sorted(
            simulated,
            key=lambda x: (
                -x["impact_analysis"]["emissions_saved_kg"],
                -x["impact_analysis"]["sustainability_conformance_change"],
                -x["impact_analysis"]["esg_improvement"],
                -x["impact_analysis"]["fitness_change"],
                -x["confidence"]
            )
        )[0]

        # 2. Best ESG Strategy: ESG Improvement (descending)
        best_esg = sorted(
            simulated,
            key=lambda x: (
                -x["impact_analysis"]["esg_improvement"],
                -x["impact_analysis"]["emissions_saved_kg"],
                -x["impact_analysis"]["sustainability_conformance_change"],
                -x["impact_analysis"]["fitness_change"],
                -x["confidence"]
            )
        )[0]

        # 3. Best Balanced Strategy: Conformance Improvement (descending)
        best_balanced = sorted(
            simulated,
            key=lambda x: (
                -x["impact_analysis"]["sustainability_conformance_change"],
                -x["impact_analysis"]["emissions_saved_kg"],
                -x["impact_analysis"]["esg_improvement"],
                -x["impact_analysis"]["fitness_change"],
                -x["confidence"]
            )
        )[0]

        return {
            "best_carbon_strategy": best_carbon,
            "best_esg_strategy": best_esg,
            "best_balanced_strategy": best_balanced
        }

    def generate_and_persist(self, analysis_id: UUID, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate and write an immutable Digital Twin snapshot to the database."""
        # 1. Resolve lineage first (MUST fail on any missing version)
        lineage = self._resolve_lineage(analysis_id)

        # 2. Run simulation in memory
        sim_data = self.simulate_scenario(analysis_id, scenario)
        
        # 3. Fetch latest conformance snapshot version for comparison tracking
        sc_version = lineage["source_sustainability_conformance_version"]

        # 4. Resolve next version number for digital twin simulation type
        max_version = self.db.query(
            func.max(func.json_extract(ScenarioSimulation.simulation_metadata, '$.digital_twin_version'))
        ).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'digital_twin',
            ScenarioSimulation.is_deleted == False
        ).scalar()
        next_version = (max_version or 0) + 1

        run_id = str(uuid.uuid4())
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 5. Build snapshot metadata payload
        sim_meta = {
            "simulation_type": "digital_twin",
            "scenario_name": scenario.get("action") or scenario.get("scenario_type") or "Custom Scenario",
            "baseline_version": sc_version,
            "digital_twin_version": next_version,
            "digital_twin_run_id": run_id,
            "analysis_id": str(analysis_id),
            "confidence": sim_data["confidence"],
            "confidence_band": sim_data["confidence_band"],
            "simulation_status": sim_data["simulation_status"],
            "forecast_explanation": sim_data["forecast_explanation"],
            "projected_outputs": sim_data["projected_outputs"],
            "impact_analysis": sim_data["impact_analysis"],
            "scenario_definition": scenario,
            **lineage
        }

        # 6. Deterministic Hashing
        hash_payload = {
            k: v for k, v in sim_meta.items()
            if k not in ["snapshot_hash", "snapshot_timestamp", "digital_twin_version", "digital_twin_run_id"]
        }
        payload_str = json.dumps(hash_payload, sort_keys=True)
        snapshot_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        sim_meta["snapshot_hash"] = snapshot_hash
        sim_meta["snapshot_timestamp"] = generated_at

        # Save to database
        analysis = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == analysis_id,
            ProcessAnalysis.is_deleted == False
        ).first()

        sim = ScenarioSimulation(
                tenant_id=analysis.tenant_id,
                workspace_id=analysis.workspace_id,
                project_id=analysis.project_id,
                analysis_id=analysis_id,
                scenario_name=f"Digital Twin Snapshot v{next_version} - {scenario.get('action') or scenario.get('scenario_type')}",
                scenario_description="Generated Digital Twin scenario simulation snapshot.",
            input_parameters=scenario,
            baseline_emissions=float(sim_meta["impact_analysis"]["emissions_saved_kg"] + sim_meta["projected_outputs"]["projected_emissions_kg"]),
            simulated_emissions=float(sim_meta["projected_outputs"]["projected_emissions_kg"]),
            emission_reduction=float(sim_meta["impact_analysis"]["emissions_saved_kg"]),
            reduction_percentage=float(sim_meta["impact_analysis"]["emissions_saved_pct"]),
            scenario_type=ScenarioType.EMISSION_REDUCTION.value,
            simulation_confidence_score=float(sim_data["confidence"]),
            simulation_metadata=sim_meta
        )
        self.db.add(sim)
        self.db.commit()

        mapped = sim_meta.copy()
        mapped["digital_twin_id"] = str(sim.id)
        return mapped

    def get_latest(self, analysis_id: UUID) -> Dict[str, Any]:
        """Fetch the latest digital twin simulation snapshot. Returns None if no snapshot exists."""
        max_version = self.db.query(
            func.max(func.json_extract(ScenarioSimulation.simulation_metadata, '$.digital_twin_version'))
        ).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'digital_twin',
            ScenarioSimulation.is_deleted == False
        ).scalar()

        if max_version is None:
            return None

        sim = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'digital_twin',
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.digital_twin_version') == max_version,
            ScenarioSimulation.is_deleted == False
        ).first()

        mapped = sim.simulation_metadata.copy()
        mapped["digital_twin_id"] = str(sim.id)
        return mapped

    def get_version(self, analysis_id: UUID, version: int) -> Dict[str, Any]:
        """Fetch a specific digital twin simulation snapshot by version."""
        sim = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'digital_twin',
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.digital_twin_version') == version,
            ScenarioSimulation.is_deleted == False
        ).first()

        if not sim:
            raise ValueError("Digital twin snapshot version not found")

        mapped = sim.simulation_metadata.copy()
        mapped["digital_twin_id"] = str(sim.id)
        return mapped

    def get_history(self, analysis_id: UUID) -> List[Dict[str, Any]]:
        """Fetch history of all digital twin simulation snapshots, ordered newest-first."""
        sims = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'digital_twin',
            ScenarioSimulation.is_deleted == False
        ).order_by(ScenarioSimulation.created_at.desc()).all()

        history = []
        for sim in sims:
            mapped = sim.simulation_metadata.copy()
            mapped["digital_twin_id"] = str(sim.id)
            history.append(mapped)
        return history

    def _resolve_lineage(self, analysis_id: UUID) -> Dict[str, int]:
        """Resolve all 9 lineage source version numbers. Fails with descriptive ValueError listing all missing sources."""
        missing = []

        # 1. Resolve analysis
        analysis = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == analysis_id,
            ProcessAnalysis.is_deleted == False
        ).first()
        if not analysis:
            raise ValueError("Analysis record not found. Please ensure the process analysis exists.")

        # 2. Reference Model
        ref_model = self.db.query(ReferenceModel).filter(
            ReferenceModel.project_id == analysis.project_id
        ).order_by(ReferenceModel.version.desc()).first()
        source_reference_model_version = None
        if not ref_model:
            missing.append("Reference Model (upload a reference model in the project)")
        else:
            source_reference_model_version = ref_model.version

        # 3. OCEL Version
        source_ocel_version = None
        try:
            ocel_latest = OcelGenerationService(self.db).get_latest(analysis_id)
            source_ocel_version = ocel_latest.get("ocel_version") if ocel_latest else None
            if source_ocel_version is None:
                missing.append("OCEL 2.0 Export (run OCEL generation from the OCEL page)")
        except Exception:
            missing.append("OCEL 2.0 Export (run OCEL generation from the OCEL page)")

        # 4. Conformance Version
        source_conformance_version = None
        try:
            conformance_latest = ObjectConformanceService(self.db).get_latest(analysis_id)
            source_conformance_version = conformance_latest.get("object_conformance_version") if conformance_latest else None
            if source_conformance_version is None:
                missing.append("Object Conformance Analysis (run conformance check from the Conformance page)")
        except Exception:
            missing.append("Object Conformance Analysis (run conformance check from the Conformance page)")

        # 5. Carbon Version
        source_carbon_version = None
        try:
            carbon_latest = ObjectCarbonAttributionService(self.db).get_latest(analysis_id)
            source_carbon_version = carbon_latest.get("object_carbon_version") if carbon_latest else None
            if source_carbon_version is None:
                missing.append("Object Carbon Attribution (run carbon attribution analysis)")
        except Exception:
            missing.append("Object Carbon Attribution (run carbon attribution analysis)")

        # 6. Interaction Version
        source_interaction_version = None
        try:
            interaction_latest = ObjectInteractionService(self.db).get_latest(analysis_id)
            source_interaction_version = interaction_latest.get("object_interaction_version") if interaction_latest else None
            if source_interaction_version is None:
                missing.append("Object Interaction Analysis (run interaction analysis)")
        except Exception:
            missing.append("Object Interaction Analysis (run interaction analysis)")

        # 7. Simulation Version
        source_simulation_version = None
        try:
            simulation_latest = ObjectSimulationService(self.db).get_latest(analysis_id)
            source_simulation_version = simulation_latest.get("simulation_version") if simulation_latest else None
            if source_simulation_version is None:
                missing.append("Object Simulation (run scenario simulation)")
        except Exception:
            missing.append("Object Simulation (run scenario simulation)")

        # 8. Interoperability Version
        source_interoperability_version = None
        try:
            interop_hist = OcelInteroperabilityService(self.db).get_import_history(analysis_id)
            if not interop_hist:
                missing.append("OCEL Interoperability Import (perform an OCEL import from the OCEL Interoperability page)")
            else:
                source_interoperability_version = interop_hist[0].get("import_version")
                if source_interoperability_version is None:
                    missing.append("OCEL Interoperability Import (perform an OCEL import from the OCEL Interoperability page)")
        except Exception:
            missing.append("OCEL Interoperability Import (perform an OCEL import from the OCEL Interoperability page)")

        # 9. Carbon Fitness Version
        source_carbon_fitness_version = None
        try:
            carbon_fitness_latest = CarbonFitnessService(self.db).get_latest(analysis_id)
            source_carbon_fitness_version = carbon_fitness_latest.get("fitness_version") if carbon_fitness_latest else None
            if source_carbon_fitness_version is None:
                missing.append("Carbon Fitness Analysis (run carbon fitness from the Carbon Fitness page)")
        except Exception:
            missing.append("Carbon Fitness Analysis (run carbon fitness from the Carbon Fitness page)")

        # 10. Sustainability Conformance Version
        source_sustainability_conformance_version = None
        try:
            sc_version = self.db.query(
                func.max(func.json_extract(ScenarioSimulation.simulation_metadata, '$.sustainability_conformance_version'))
            ).filter(
                ScenarioSimulation.analysis_id == analysis_id,
                ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
                func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'sustainability_conformance',
                ScenarioSimulation.is_deleted == False
            ).scalar()
            if sc_version is None:
                missing.append("Sustainability Conformance Snapshot (run Sustainability Conformance first)")
            else:
                source_sustainability_conformance_version = sc_version
        except Exception:
            missing.append("Sustainability Conformance Snapshot (run Sustainability Conformance first)")

        if missing:
            missing_list = "; ".join(missing)
            raise ValueError(
                f"Cannot generate Digital Twin — the following prerequisites are missing: {missing_list}. "
                f"Please complete all required upstream analyses before running the Digital Twin."
            )

        return {
            "source_reference_model_version": source_reference_model_version,
            "source_ocel_version": source_ocel_version,
            "source_conformance_version": source_conformance_version,
            "source_carbon_version": source_carbon_version,
            "source_interaction_version": source_interaction_version,
            "source_simulation_version": source_simulation_version,
            "source_interoperability_version": source_interoperability_version,
            "source_carbon_fitness_version": source_carbon_fitness_version,
            "source_sustainability_conformance_version": source_sustainability_conformance_version
        }
