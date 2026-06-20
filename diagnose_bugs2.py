"""
Deeper diagnostic - fix the created_at issue and investigate more
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_PATH = os.path.join(os.path.dirname(__file__), "sustainocpm.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)
db = Session()

analysis_id = "fdd13aabf1284bc09cb46f338d795270"
workspace_id = "0b7e285f0a6041438be4dfd951145ae5"
tenant_id = "e14d346d6f854757bda02c14065d739d"

print("=" * 70)
print("DEEP DIAGNOSTIC REPORT")
print("=" * 70)

# 1. Check esg_scores schema
print("\n--- ESG_SCORES TABLE SCHEMA ---")
cols = db.execute(text("PRAGMA table_info(esg_scores)")).fetchall()
for col in cols:
    print(f"  col: {col[1]} ({col[2]})")

# 2. ESG scores data
print("\n--- ESG SCORES DATA ---")
esg_scores = db.execute(text(
    "SELECT id, overall_score, environmental_score, social_score, governance_score, period FROM esg_scores "
    "WHERE workspace_id=:wid AND is_deleted=0 LIMIT 5"
), {"wid": workspace_id}).fetchall()
if not esg_scores:
    print("  WARNING: No ESG scores found!")
else:
    for r in esg_scores:
        print(f"  ID={r[0]} | overall={r[1]} | E={r[2]} | S={r[3]} | G={r[4]} | period={r[5]}")

# 3. ESG KPI values detail
print("\n--- ESG KPI VALUES DETAIL ---")
kpi_vals = db.execute(text(
    "SELECT kpi_definition_id, value, period, workspace_id FROM esg_kpi_values WHERE tenant_id=:tid AND is_deleted=0 LIMIT 10"
), {"tid": tenant_id}).fetchall()
for r in kpi_vals:
    print(f"  kpi_def_id={r[0]} | value={r[1]} | period={r[2]} | ws={r[3]}")

# 4. ESG KPI definitions detail
print("\n--- ESG KPI DEFINITIONS ---")
kpi_defs = db.execute(text(
    "SELECT id, kpi_code, name, category FROM esg_kpi_definitions WHERE tenant_id=:tid AND is_active=1 AND is_deleted=0"
), {"tid": tenant_id}).fetchall()
for r in kpi_defs:
    print(f"  id={r[0]} | code={r[1]} | name={r[2]} | category={r[3]}")

# 5. Carbon fitness snapshot detail
print("\n--- CARBON FITNESS SNAPSHOT DETAIL ---")
cf = db.execute(text(
    "SELECT id, simulation_metadata FROM scenario_simulations "
    "WHERE analysis_id=:aid AND json_extract(simulation_metadata, '$.simulation_type')='carbon_fitness' AND is_deleted=0"
), {"aid": analysis_id}).fetchone()
if cf:
    import json
    meta = json.loads(cf[1]) if isinstance(cf[1], str) else cf[1]
    print(f"  ID={cf[0]}")
    print(f"  fitness_version={meta.get('fitness_version')}")
    print(f"  process_fitness={meta.get('process_fitness')}")
    print(f"  carbon_fitness={meta.get('carbon_fitness')}")
    print(f"  sustainability_fitness={meta.get('sustainability_fitness')}")
    print(f"  carbon_budget_kg={meta.get('carbon_budget_kg')}")
    print(f"  actual_emissions_kg={meta.get('actual_emissions_kg')}")
    print(f"  violations count={len(meta.get('violations', []))}")
else:
    print("  No carbon fitness snapshot!")

# 6. Object carbon attribution detail
print("\n--- OBJECT CARBON ATTRIBUTION DETAIL ---")
oca = db.execute(text(
    "SELECT id, simulation_metadata FROM scenario_simulations "
    "WHERE analysis_id=:aid AND json_extract(simulation_metadata, '$.simulation_type')='object_carbon_attribution' AND is_deleted=0"
), {"aid": analysis_id}).fetchone()
if oca:
    import json
    meta = json.loads(oca[1]) if isinstance(oca[1], str) else oca[1]
    print(f"  ID={oca[0]}")
    print(f"  object_carbon_version={meta.get('object_carbon_version')}")
    print(f"  total_object_emissions={meta.get('total_object_emissions')}")
    print(f"  total_events_count={meta.get('total_events_count')}")
    objects = meta.get("objects", [])
    print(f"  objects count={len(objects)}")
else:
    print("  No object carbon attribution snapshot!")

# 7. Object conformance detail
print("\n--- OBJECT CONFORMANCE DETAIL ---")
oc = db.execute(text(
    "SELECT id, simulation_metadata FROM scenario_simulations "
    "WHERE analysis_id=:aid AND json_extract(simulation_metadata, '$.simulation_type')='object_conformance' AND is_deleted=0"
), {"aid": analysis_id}).fetchone()
if oc:
    import json
    meta = json.loads(oc[1]) if isinstance(oc[1], str) else oc[1]
    print(f"  ID={oc[0]}")
    print(f"  object_conformance_version={meta.get('object_conformance_version')}")
    print(f"  average_fitness={meta.get('average_fitness')}")
    print(f"  total_objects={meta.get('total_objects')}")
else:
    print("  No object conformance snapshot!")

# 8. Sustainability conformance detail
print("\n--- SUSTAINABILITY CONFORMANCE DETAIL ---")
sc = db.execute(text(
    "SELECT id, simulation_metadata FROM scenario_simulations "
    "WHERE analysis_id=:aid AND json_extract(simulation_metadata, '$.simulation_type')='sustainability_conformance' AND is_deleted=0"
), {"aid": analysis_id}).fetchone()
if sc:
    import json
    meta = json.loads(sc[1]) if isinstance(sc[1], str) else sc[1]
    print(f"  ID={sc[0]}")
    print(f"  conformance_score={meta.get('conformance_score')}")
    print(f"  esg_compliance_score={meta.get('esg_compliance_score')}")
    print(f"  sustainability_risk={meta.get('sustainability_risk')}")
else:
    print("  No sustainability conformance snapshot for this analysis! (may need generation)")

# 9. Check all analyses and their carbon fitness scenario_type
print("\n--- SCENARIO_SIMULATION scenario_type values ---")
st_vals = db.execute(text(
    "SELECT DISTINCT scenario_type FROM scenario_simulations WHERE analysis_id=:aid AND is_deleted=0"
), {"aid": analysis_id}).fetchall()
for r in st_vals:
    print(f"  scenario_type={r[0]}")

# 10. Check benchmark user context
print("\n--- USERS AND ROLES ---")
users = db.execute(text("SELECT id, email FROM users LIMIT 5")).fetchall()
for r in users:
    print(f"  user_id={r[0]} | email={r[1]}")

roles = db.execute(text("SELECT user_id, organization_id, role FROM user_roles LIMIT 5")).fetchall()
for r in roles:
    print(f"  user_id={r[0]} | org_id={r[1]} | role={r[2]}")

db.close()
print("\n" + "=" * 70)
