import os
import sys
import uuid
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models import CarbonSimulation, SustainabilityConformance, ESGScore, Workspace

db = SessionLocal()
ws = db.query(Workspace).first()
analysis_uuid = uuid.UUID("f337b9ad-d36c-4ce7-b155-2d87a3bfae79")

carbon = db.query(CarbonSimulation).filter(CarbonSimulation.analysis_id == analysis_uuid).order_by(CarbonSimulation.created_at.desc()).first()
sustain = db.query(SustainabilityConformance).filter(SustainabilityConformance.analysis_id == analysis_uuid).order_by(SustainabilityConformance.created_at.desc()).first()
esg = db.query(ESGScore).filter(ESGScore.workspace_id == ws.id).order_by(ESGScore.calculated_at.desc()).first()

print("--- DB EVIDENCE ---")
print("Total Emissions:", carbon.actual_emissions_kg if carbon else None)
print("Carbon Fitness:", carbon.fitness_score if carbon else None)
print("Process Fitness:", sustain.process_fitness if sustain else None)
print("Sustainability Conformance:", sustain.sustainability_conformance if sustain else None)
print("ESG Score:", esg.overall_score if esg else None)
print("-------------------")
