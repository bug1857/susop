import os
import sys
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import SessionLocal
from app.models.models import ScenarioSimulation

db = SessionLocal()
analysis_id = "4127d16c-2f76-4cea-88db-b5d2b9849fce"

sim = db.query(ScenarioSimulation).filter(
    ScenarioSimulation.id == uuid.UUID("02631561-6de1-4140-a68e-85798d6c2cd1")
).first()

print(sim.simulation_metadata.get("simulation_type"))
