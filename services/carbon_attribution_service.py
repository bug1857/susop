import json
import time
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
import pandas as pd

from app.models.models import (
    CarbonAttribution,
    EmissionHotspot,
    ProcessAnalysis,
    ProcessVariant
)
from app.repositories.carbon_attribution_repository import CarbonAttributionRepository
from app.repositories.emission_factor_repository import EmissionFactorRepository
from app.core.ocel_parser import parse_dataset_to_dataframe
from app.core.audit import log_activity
from app.services.carbon_fitness_service import CarbonFitnessService

class CarbonAttributionService:
    def __init__(self, db: Session):
        self.db = db
        self.attr_repo = CarbonAttributionRepository(db)
        self.factor_repo = EmissionFactorRepository(db)
        self.fitness_service = CarbonFitnessService(db)

    def calculate_carbon_attribution(self, analysis_id: UUID, tenant_id: UUID) -> dict:
        log_activity(self.db, user_id=UUID("00000000-0000-0000-0000-00000000000a"), action="carbon_attribution_started", tenant_id=tenant_id, details=f"Started carbon attribution for analysis {analysis_id}")
        
        # 1. Fetch Analysis
        analysis = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == analysis_id,
            ProcessAnalysis.tenant_id == tenant_id
        ).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Process analysis not found")

        try:
            # 2. Parse dataset to DataFrame
            df = parse_dataset_to_dataframe(analysis.dataset_id, tenant_id, analysis.workspace_id, self.db)
            if df.empty:
                raise Exception("Event log is empty")

            # Validate carbon column if present
            has_carbon_col = "carbon_emissions" in df.columns
            if has_carbon_col:
                try:
                    df["carbon_emissions"] = pd.to_numeric(df["carbon_emissions"])
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid carbon column: non-numeric values detected. Details: {str(e)}")

            # 3. Resolve factors and calculate emissions per event
            unique_activities = df["concept:name"].unique()
            resolved_factors = {}
            
            # Resolve factors first (Raise error if any is missing to satisfy error handling requirement)
            for activity in unique_activities:
                factor = self.factor_repo.resolve_factor(activity, tenant_id)
                if not factor:
                    raise HTTPException(status_code=400, detail=f"Missing emission factor for activity: {activity}")
                resolved_factors[activity] = factor

            # Calculate event emissions
            event_emissions = []
            for _, row in df.iterrows():
                activity = row["concept:name"]
                factor = resolved_factors[activity]
                event_val = float(row["carbon_emissions"]) if has_carbon_col else 1.0
                event_emissions.append(event_val * factor.factor_value)
            
            df["event_emissions"] = event_emissions

            # 4. Aggregated Activity Emissions & Save CarbonAttribution
            # Clear old attributions if they exist for this run
            self.db.query(CarbonAttribution).filter(CarbonAttribution.analysis_id == analysis_id).delete()
            
            activity_groups = df.groupby("concept:name")["event_emissions"].sum().to_dict()
            total_analysis_emissions = sum(activity_groups.values())

            attrs_to_insert = []
            for activity, emissions in activity_groups.items():
                factor = resolved_factors[activity]
                attr = CarbonAttribution(
                    id=uuid4(),
                    analysis_id=analysis_id,
                    tenant_id=tenant_id,
                    workspace_id=analysis.workspace_id,
                    project_id=analysis.project_id,
                    activity_name=activity,
                    emission_factor_id=factor.id,
                    emissions=float(emissions),
                    created_at=datetime.utcnow()
                )
                attrs_to_insert.append(attr)

            if attrs_to_insert:
                self.attr_repo.create_all(attrs_to_insert)


            log_activity(self.db, user_id=UUID("00000000-0000-0000-0000-00000000000a"), action="carbon_attribution_completed", tenant_id=tenant_id, details=f"Calculated activity emissions. Total: {total_analysis_emissions:.2f}")

            # 5. Variant Emissions calculation and update
            # Calculate total emissions per case
            case_emissions = df.groupby("case:concept:name")["event_emissions"].sum()
            
            # Group cases by variant activity sequences
            df_sorted = df.sort_values(by=["case:concept:name", "time:timestamp"])
            case_sequences = df_sorted.groupby("case:concept:name")["concept:name"].apply(list)
            
            variants = self.db.query(ProcessVariant).filter(
                ProcessVariant.analysis_id == analysis_id
            ).all()

            for var in variants:
                # Find cases matching this sequence
                matching_cases = []
                for case_id, seq in case_sequences.items():
                    if seq == var.activity_sequence:
                        matching_cases.append(case_id)
                
                if matching_cases:
                    emissions_sub = case_emissions.loc[matching_cases]
                    var.total_emissions = float(emissions_sub.sum())
                    var.average_emissions = float(emissions_sub.mean())
                    var.emissions_per_execution = float(var.total_emissions / var.frequency) if var.frequency > 0 else 0.0
                    self.db.add(var)
            
            self.db.commit()

            # 6. Emission Hotspot Detection
            self.db.query(EmissionHotspot).filter(EmissionHotspot.analysis_id == analysis_id).delete()
            for activity, emissions in activity_groups.items():
                contrib = (emissions / total_analysis_emissions * 100) if total_analysis_emissions > 0 else 0.0
                
                # Severity Rules
                if contrib >= 30.0:
                    sev = "Critical"
                elif contrib >= 20.0:
                    sev = "High"
                elif contrib >= 10.0:
                    sev = "Medium"
                else:
                    sev = "Low"

                hotspot = EmissionHotspot(
                    id=uuid4(),
                    analysis_id=analysis_id,
                    tenant_id=tenant_id,
                    workspace_id=analysis.workspace_id,
                    project_id=analysis.project_id,
                    activity_name=activity,
                    emissions=float(emissions),
                    contribution_percentage=contrib,
                    severity=sev,
                    created_at=datetime.utcnow()
                )
                self.db.add(hotspot)
                self.db.commit()
                
                log_activity(self.db, user_id=UUID("00000000-0000-0000-0000-00000000000a"), action="hotspot_detected", tenant_id=tenant_id, details=f"Detected hotspot: {activity} ({contrib:.1f}%, Severity: {sev})")

            # 7. Carbon Budget Evaluation and Carbon Fitness Score calculation
            fitness_res = self.fitness_service.calculate_carbon_fitness(
                analysis_id=analysis_id,
                tenant_id=tenant_id,
                actual_emissions=total_analysis_emissions
            )

            # Build explainability payload
            explainability = []
            for activity, factor in resolved_factors.items():
                explainability.append({
                    "activity": activity,
                    "factor_source": factor.source_name,
                    "source_version": factor.source_version,
                    "calculation_inputs": {
                        "event_value": "mapped_carbon_emissions" if has_carbon_col else "event_count",
                        "factor_value": factor.factor_value
                    },
                    "calculation_formula": "activity_emissions = event_value * factor_value"
                })

            return {
                "status": "completed",
                "total_emissions": total_analysis_emissions,
                "fitness_results": fitness_res,
                "explainability": explainability
            }

        except Exception as e:
            log_activity(self.db, user_id=UUID("00000000-0000-0000-0000-00000000000a"), action="carbon_attribution_failed", tenant_id=tenant_id, details=f"Failed: {str(e)[:400]}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Carbon attribution failed: {str(e)}")
