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

class SustainabilityConformanceService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_sustainability_conformance(self, analysis_id: UUID) -> float:
        """Calculate the unified sustainability conformance score."""
        # 1. Fetch Process Fitness
        from app.services.object_conformance_service import ObjectConformanceService
        conformance_summary = ObjectConformanceService(self.db).get_summary(analysis_id)
        process_fitness = conformance_summary.get("average_fitness", 0.0)

        # 2. Fetch Carbon Fitness
        from app.services.carbon_fitness_service import CarbonFitnessService
        carbon_service = CarbonFitnessService(self.db)
        fit_data = carbon_service.calculate_object_carbon_fitness(analysis_id)
        carbon_fitness = fit_data.get("carbon_fitness", 0.0)

        # 3. Base Score calculation
        base_score = (0.6 * process_fitness) + (0.4 * carbon_fitness)

        # 4. Fetch green violations and apply penalties
        violations = carbon_service.detect_green_violations(analysis_id)
        total_penalty = 0.0
        for v in violations:
            severity = v.get("severity", "LOW").upper()
            if severity == "LOW":
                total_penalty += 0.02
            elif severity == "MEDIUM":
                total_penalty += 0.05
            elif severity == "HIGH":
                total_penalty += 0.10
            elif severity == "CRITICAL":
                total_penalty += 0.20

        # Cap penalty at 0.60
        total_penalty = min(total_penalty, 0.60)

        # 5. Final score
        conformance_score = base_score - total_penalty
        return max(0.0, min(1.0, conformance_score))

    def calculate_esg_compliance_score(self, analysis_id: UUID) -> float:
        """Calculate the ESG Compliance score (0-100) from official ESG service."""
        from app.models.models import ProcessAnalysis, EsgScore
        
        analysis = self.db.query(ProcessAnalysis).filter(ProcessAnalysis.id == analysis_id).first()
        if not analysis:
            return 0.0

        latest_score = self.db.query(EsgScore).filter(
            EsgScore.workspace_id == analysis.workspace_id,
            EsgScore.is_deleted == False
        ).order_by(EsgScore.calculated_at.desc()).first()

        if latest_score:
            return latest_score.overall_score
            
        return 0.0

    def detect_sustainability_deviations(self, analysis_id: UUID) -> List[Dict[str, Any]]:
        """Detect sustainability deviations with severities, impact scores, and recommendations."""
        deviations = []

        # 1. Fetch Fitness & Violations
        from app.services.object_conformance_service import ObjectConformanceService
        conformance_summary = ObjectConformanceService(self.db).get_summary(analysis_id)
        process_fitness = conformance_summary.get("average_fitness", 0.0)

        from app.services.carbon_fitness_service import CarbonFitnessService
        carbon_service = CarbonFitnessService(self.db)
        fit_data = carbon_service.calculate_object_carbon_fitness(analysis_id)
        carbon_fitness = fit_data.get("carbon_fitness", 0.0)

        violations = carbon_service.detect_green_violations(analysis_id)
        violations_types = [v.get("violation_type") for v in violations]

        # Deviation 1: PROCESS_NON_COMPLIANCE
        if process_fitness < 0.85:
            severity = "HIGH" if process_fitness < 0.70 else "MEDIUM"
            deviations.append({
                "type": "PROCESS_NON_COMPLIANCE",
                "severity": severity,
                "description": f"Process conformance average fitness ({process_fitness:.2f}) is below 85% threshold.",
                "impact_score": round((1.0 - process_fitness) * 100.0, 2),
                "recommended_action": "Remediate process deviations and optimize process flows."
            })

        # Deviation 2: CARBON_BUDGET_BREACH
        if carbon_fitness < 1.0 or "CARBON_BUDGET_EXCEEDED" in violations_types:
            deviations.append({
                "type": "CARBON_BUDGET_BREACH",
                "severity": "HIGH",
                "description": "Actual carbon emissions exceed the target carbon budget.",
                "impact_score": 40.0,
                "recommended_action": "Reduce transport distances and optimize logistics routing."
            })

        # Deviation 3: HIGH_EMISSION_SUPPLIER
        if "HIGH_EMISSION_SUPPLIER" in violations_types:
            deviations.append({
                "type": "HIGH_EMISSION_SUPPLIER",
                "severity": "MEDIUM",
                "description": "Supply chain detects one or more suppliers with high emissions.",
                "impact_score": 30.0,
                "recommended_action": "Transition procurement to certified low-carbon suppliers."
            })

        # Deviation 4: UNNECESSARY_AIR_FREIGHT
        if "UNNECESSARY_AIR_FREIGHT" in violations_types:
            deviations.append({
                "type": "UNNECESSARY_AIR_FREIGHT",
                "severity": "HIGH",
                "description": "Shipments are using high-emission air freight unnecessarily.",
                "impact_score": 35.0,
                "recommended_action": "Shift logistics modes from air freight to sea or rail."
            })

        # Deviation 5: ROUTE_EMISSION_EXCESS
        if "HIGH_EMISSION_ROUTE" in violations_types or "EXCESSIVE_TRANSPORT_DISTANCE" in violations_types:
            deviations.append({
                "type": "ROUTE_EMISSION_EXCESS",
                "severity": "MEDIUM",
                "description": "Active route emissions or transport distances exceed limits.",
                "impact_score": 25.0,
                "recommended_action": "Source materials regionally to reduce transit mileage."
            })

        # Deviation 6: LOW_SUSTAINABILITY_SCORE
        score = self.calculate_sustainability_conformance(analysis_id)
        if score < 0.70:
            severity = "HIGH" if score < 0.50 else "MEDIUM"
            deviations.append({
                "type": "LOW_SUSTAINABILITY_SCORE",
                "severity": severity,
                "description": f"Overall sustainability conformance score ({score:.2f}) is below target threshold.",
                "impact_score": 50.0,
                "recommended_action": "Review top emission hotspots and process bottlenecks to increase efficiency."
            })

        return deviations

    def classify_sustainability_risk(self, analysis_id: UUID) -> str:
        """Classify sustainability risk (LOW, MEDIUM, HIGH, CRITICAL)."""
        score = self.calculate_sustainability_conformance(analysis_id)
        esg_score = self.calculate_esg_compliance_score(analysis_id)

        from app.services.carbon_fitness_service import CarbonFitnessService
        violations = CarbonFitnessService(self.db).detect_green_violations(analysis_id)
        has_critical_violation = any(v.get("severity") == "CRITICAL" for v in violations)

        if has_critical_violation or score < 0.40:
            return "CRITICAL"
        elif score < 0.65 or len(violations) >= 3:
            return "HIGH"
        elif score < 0.80 or len(violations) >= 1:
            return "MEDIUM"
        return "LOW"

    def generate_and_persist(self, analysis_id: UUID) -> Dict[str, Any]:
        """Create and persist an immutable Sustainability Conformance snapshot."""
        # 1. Fetch analysis details
        analysis = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == analysis_id,
            ProcessAnalysis.is_deleted == False
        ).first()
        if not analysis:
            raise ValueError("Analysis not found")

        # 2. Resolve Lineage sources (MUST FAIL if any lineage source cannot be resolved)
        lineage = self._resolve_lineage(analysis_id)

        # 3. Calculate scores & deviations
        from app.services.object_conformance_service import ObjectConformanceService
        conformance_summary = ObjectConformanceService(self.db).get_summary(analysis_id)
        process_fitness = conformance_summary.get("average_fitness", 0.0)

        from app.services.carbon_fitness_service import CarbonFitnessService
        carbon_fitness_data = CarbonFitnessService(self.db).calculate_object_carbon_fitness(analysis_id)
        carbon_fitness = carbon_fitness_data.get("carbon_fitness", 0.0)

        conformance_score = self.calculate_sustainability_conformance(analysis_id)
        esg_score = self.calculate_esg_compliance_score(analysis_id)
        risk_level = self.classify_sustainability_risk(analysis_id)
        deviations = self.detect_sustainability_deviations(analysis_id)

        # 4. Resolve next version number
        max_version = self.db.query(
            func.max(func.json_extract(ScenarioSimulation.simulation_metadata, '$.sustainability_conformance_version'))
        ).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'sustainability_conformance',
            ScenarioSimulation.is_deleted == False
        ).scalar()
        next_version = (max_version or 0) + 1

        run_id = str(uuid.uuid4())
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 5. Build snapshot metadata payload
        sim_meta = {
            "simulation_type": "sustainability_conformance",
            "sustainability_conformance_version": next_version,
            "sustainability_conformance_run_id": run_id,
            "analysis_id": str(analysis_id),
            "process_fitness": round(process_fitness, 2),
            "carbon_fitness": round(carbon_fitness, 2),
            "sustainability_conformance": round(conformance_score, 2),
            "esg_compliance_score": round(esg_score, 2),
            "sustainability_risk": risk_level,
            "deviations": deviations,
            **lineage
        }

        # 6. Deterministic Hashing: Exclude UTC timestamp & version number & run id
        hash_payload = {
            k: v for k, v in sim_meta.items()
            if k not in ["snapshot_hash", "snapshot_timestamp", "sustainability_conformance_version", "sustainability_conformance_run_id"]
        }
        payload_str = json.dumps(hash_payload, sort_keys=True)
        snapshot_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        sim_meta["snapshot_hash"] = snapshot_hash
        sim_meta["snapshot_timestamp"] = generated_at

        # Save to database
        sim = ScenarioSimulation(
            tenant_id=analysis.tenant_id,
            workspace_id=analysis.workspace_id,
            project_id=analysis.project_id,
            analysis_id=analysis_id,
            scenario_name=f"Sustainability Conformance Snapshot v{next_version}",
            scenario_description="Generated Sustainability Conformance checking snapshot.",
            input_parameters={},
            baseline_emissions=0.0,
            simulated_emissions=0.0,
            emission_reduction=0.0,
            reduction_percentage=0.0,
            scenario_type=ScenarioType.EMISSION_REDUCTION.value,
            simulation_confidence_score=100.0,
            simulation_metadata=sim_meta
        )
        self.db.add(sim)
        self.db.commit()

        mapped = sim_meta.copy()
        mapped["sustainability_conformance_id"] = str(sim.id)
        return mapped

    def get_latest(self, analysis_id: UUID) -> Dict[str, Any]:
        """Fetch the latest snapshot metadata. Returns None if no snapshot has been calculated yet."""
        max_version = self.db.query(
            func.max(func.json_extract(ScenarioSimulation.simulation_metadata, '$.sustainability_conformance_version'))
        ).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'sustainability_conformance',
            ScenarioSimulation.is_deleted == False
        ).scalar()

        if max_version is None:
            # Auto-generate if missing
            return self.generate_and_persist(analysis_id)

        sim = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'sustainability_conformance',
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.sustainability_conformance_version') == max_version,
            ScenarioSimulation.is_deleted == False
        ).first()

        mapped = sim.simulation_metadata.copy()
        mapped["sustainability_conformance_id"] = str(sim.id)
        return mapped

    def get_version(self, analysis_id: UUID, version: int) -> Dict[str, Any]:
        """Fetch a specific snapshot metadata by version."""
        sim = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'sustainability_conformance',
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.sustainability_conformance_version') == version,
            ScenarioSimulation.is_deleted == False
        ).first()

        if not sim:
            raise ValueError("Sustainability conformance snapshot version not found")

        mapped = sim.simulation_metadata.copy()
        mapped["sustainability_conformance_id"] = str(sim.id)
        return mapped

    def get_history(self, analysis_id: UUID) -> List[Dict[str, Any]]:
        """Fetch history of all snapshots, ordered newest-first."""
        sims = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.EMISSION_REDUCTION.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'sustainability_conformance',
            ScenarioSimulation.is_deleted == False
        ).order_by(ScenarioSimulation.created_at.desc()).all()

        history = []
        for sim in sims:
            mapped = sim.simulation_metadata.copy()
            mapped["sustainability_conformance_id"] = str(sim.id)
            history.append(mapped)
        return history

    def _resolve_lineage(self, analysis_id: UUID) -> Dict[str, int]:
        """Resolve all 8 source layers version numbers. Fails with descriptive ValueError if any source cannot be resolved."""
        from app.services.ocel_service import OcelGenerationService
        from app.services.object_conformance_service import ObjectConformanceService
        from app.services.object_carbon_service import ObjectCarbonAttributionService
        from app.services.object_interaction_service import ObjectInteractionService
        from app.services.object_simulation_service import ObjectSimulationService
        from app.services.ocel_interoperability_service import OcelInteroperabilityService
        from app.services.carbon_fitness_service import CarbonFitnessService

        missing = []

        analysis = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == analysis_id,
            ProcessAnalysis.is_deleted == False
        ).first()
        if not analysis:
            raise ValueError("Analysis record not found. Please ensure the process analysis exists.")

        ref_model = self.db.query(ReferenceModel).filter(
            ReferenceModel.project_id == analysis.project_id
        ).order_by(ReferenceModel.version.desc()).first()

        source_reference_model_version = None
        if not ref_model:
            missing.append("Reference Model (upload a reference model in the project)")
        else:
            source_reference_model_version = ref_model.version

        source_ocel_version = None
        try:
            ocel_latest = OcelGenerationService(self.db).get_latest(analysis_id)
            source_ocel_version = ocel_latest.get("ocel_version") if ocel_latest else None
            if source_ocel_version is None:
                missing.append("OCEL 2.0 Export (run OCEL generation from the OCEL page)")
        except Exception:
            missing.append("OCEL 2.0 Export (run OCEL generation from the OCEL page)")

        source_conformance_version = None
        try:
            conformance_latest = ObjectConformanceService(self.db).get_latest(analysis_id)
            source_conformance_version = conformance_latest.get("object_conformance_version") if conformance_latest else None
            if source_conformance_version is None:
                missing.append("Object Conformance Analysis (run conformance check from the Conformance page)")
        except Exception:
            missing.append("Object Conformance Analysis (run conformance check from the Conformance page)")

        source_carbon_version = None
        try:
            carbon_latest = ObjectCarbonAttributionService(self.db).get_latest(analysis_id)
            source_carbon_version = carbon_latest.get("object_carbon_version") if carbon_latest else None
            if source_carbon_version is None:
                missing.append("Object Carbon Attribution (run carbon attribution analysis)")
        except Exception:
            missing.append("Object Carbon Attribution (run carbon attribution analysis)")

        source_interaction_version = None
        try:
            interaction_latest = ObjectInteractionService(self.db).get_latest(analysis_id)
            source_interaction_version = interaction_latest.get("object_interaction_version") if interaction_latest else None
            if source_interaction_version is None:
                missing.append("Object Interaction Analysis (run interaction analysis)")
        except Exception:
            missing.append("Object Interaction Analysis (run interaction analysis)")

        source_simulation_version = None
        try:
            simulation_latest = ObjectSimulationService(self.db).get_latest(analysis_id)
            source_simulation_version = simulation_latest.get("simulation_version") if simulation_latest else None
            if source_simulation_version is None:
                missing.append("Object Simulation (run scenario simulation)")
        except Exception:
            missing.append("Object Simulation (run scenario simulation)")

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

        source_carbon_fitness_version = None
        try:
            carbon_fitness_latest = CarbonFitnessService(self.db).get_latest(analysis_id)
            source_carbon_fitness_version = carbon_fitness_latest.get("fitness_version") if carbon_fitness_latest else None
            if source_carbon_fitness_version is None:
                missing.append("Carbon Fitness Analysis (run carbon fitness from the Carbon Fitness page)")
        except Exception:
            missing.append("Carbon Fitness Analysis (run carbon fitness from the Carbon Fitness page)")

        if missing:
            missing_list = "; ".join(missing)
            raise ValueError(
                f"Cannot calculate Sustainability Conformance — the following prerequisites are missing: {missing_list}. "
                f"Please complete all required upstream analyses before running Sustainability Conformance."
            )

        return {
            "source_reference_model_version": source_reference_model_version,
            "source_ocel_version": source_ocel_version,
            "source_conformance_version": source_conformance_version,
            "source_carbon_version": source_carbon_version,
            "source_interaction_version": source_interaction_version,
            "source_simulation_version": source_simulation_version,
            "source_interoperability_version": source_interoperability_version,
            "source_carbon_fitness_version": source_carbon_fitness_version
        }
