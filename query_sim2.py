import os
import sys
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import SessionLocal
from app.models.models import ScenarioSimulation

db = SessionLocal()
analysis_id = "4127d16c-2f76-4cea-88db-b5d2b9849fce"

sims = db.query(ScenarioSimulation).filter(
    ScenarioSimulation.analysis_id == uuid.UUID(analysis_id)
).all()

for sim in sims:
    meta = sim.simulation_metadata or {}
    print(sim.id, sim.scenario_type, meta.get("simulation_type"), meta.get("ocel_version"))
