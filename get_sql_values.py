import os
import sys
import uuid
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from sqlalchemy import text
from app.models.models import Workspace

db = SessionLocal()
ws = db.query(Workspace).first()
aid = "f337b9add36c4ce7b1552d87a3bfae79"
uid = "f337b9ad-d36c-4ce7-b155-2d87a3bfae79"

print("--- SQL EVIDENCE ---")

res = db.execute(text(f"SELECT simulation_metadata FROM scenario_simulations WHERE json_extract(simulation_metadata, '$.simulation_type') = 'object_carbon_attribution' ORDER BY created_at DESC LIMIT 1")).scalar()
print("Carbon Attribution DB:", json.dumps(json.loads(res).get("total_object_emissions") if res else None))

res = db.execute(text(f"SELECT simulation_metadata FROM scenario_simulations WHERE json_extract(simulation_metadata, '$.simulation_type') = 'carbon_fitness' ORDER BY created_at DESC LIMIT 1")).scalar()
print("Carbon Fitness DB:", json.dumps(json.loads(res).get("carbon_fitness") if res else None))

res = db.execute(text(f"SELECT simulation_metadata FROM scenario_simulations WHERE json_extract(simulation_metadata, '$.simulation_type') = 'object_conformance' ORDER BY created_at DESC LIMIT 1")).scalar()
print("Process Fitness DB:", json.dumps(json.loads(res).get("average_fitness") if res else None))

res = db.execute(text(f"SELECT simulation_metadata FROM scenario_simulations WHERE json_extract(simulation_metadata, '$.simulation_type') = 'sustainability_conformance' ORDER BY created_at DESC LIMIT 1")).scalar()
print("Sustain Conformance DB:", json.dumps(json.loads(res).get("sustainability_conformance") if res else None))

res = db.execute(text(f"SELECT overall_score FROM esg_scores ORDER BY calculated_at DESC LIMIT 1")).scalar()
print("ESG Score DB:", res)

print("--------------------")
