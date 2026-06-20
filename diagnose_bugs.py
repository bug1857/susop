"""
Diagnostic script to identify root causes of:
1. Compliance score = 0
2. Carbon fitness = NA
3. Total emissions = NA
4. Benchmark not working
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

print("=" * 70)
print("DIAGNOSTIC REPORT")
print("=" * 70)

# 1. Check active analyses
print("\n--- ACTIVE PROCESS ANALYSES ---")
rows = db.execute(text("SELECT id, workspace_id, project_id, tenant_id, is_deleted FROM process_analyses WHERE is_deleted=0 LIMIT 5")).fetchall()
if not rows:
    print("  WARNING: No active process analyses found!")
else:
    for r in rows:
        print(f"  ID={r[0]} | WS={r[1]} | Project={r[2]} | Tenant={r[3]}")

if rows:
    analysis_id = rows[0][0]
    tenant_id = rows[0][3]
    workspace_id = rows[0][1]
    print(f"\n  Using analysis_id: {analysis_id}")
    
    # 2. Check ObjectCarbonAttribution snapshots
    print("\n--- OBJECT CARBON ATTRIBUTION SNAPSHOTS ---")
    carbon_rows = db.execute(text(
        "SELECT id, analysis_id, json_extract(simulation_metadata, '$.simulation_type') as sim_type, "
        "json_extract(simulation_metadata, '$.object_carbon_version') as ver "
        "FROM scenario_simulations WHERE analysis_id=:aid AND is_deleted=0 LIMIT 10"
    ), {"aid": analysis_id}).fetchall()
    
    if not carbon_rows:
        print("  WARNING: No scenario_simulation rows for this analysis!")
    else:
        for r in carbon_rows:
            print(f"  ID={r[0]} | sim_type={r[2]} | version={r[3]}")
    
    # Check all sim_types present
    all_sims = db.execute(text(
        "SELECT json_extract(simulation_metadata, '$.simulation_type') as sim_type, COUNT(*) as cnt "
        "FROM scenario_simulations WHERE analysis_id=:aid AND is_deleted=0 "
        "GROUP BY sim_type"
    ), {"aid": analysis_id}).fetchall()
    print("\n  Simulation types present:")
    for r in all_sims:
        print(f"    {r[0]}: {r[1]} rows")
    
    # 3. Check conformance results
    print("\n--- CONFORMANCE RESULTS ---")
    conf = db.execute(text(
        "SELECT id, fitness_score, carbon_fitness_score FROM conformance_results WHERE analysis_id=:aid LIMIT 5"
    ), {"aid": analysis_id}).fetchall()
    if not conf:
        print("  WARNING: No conformance results found!")
    else:
        for r in conf:
            print(f"  ID={r[0]} | fitness_score={r[1]} | carbon_fitness_score={r[2]}")
    
    # 4. Check ESG KPI values
    print("\n--- ESG KPI VALUES (for tenant) ---")
    kpi_vals = db.execute(text(
        "SELECT COUNT(*) FROM esg_kpi_values WHERE tenant_id=:tid AND is_deleted=0"
    ), {"tid": tenant_id}).fetchone()
    print(f"  ESG KPI Values count: {kpi_vals[0]}")
    
    kpi_defs = db.execute(text(
        "SELECT COUNT(*) FROM esg_kpi_definitions WHERE tenant_id=:tid AND is_active=1 AND is_deleted=0"
    ), {"tid": tenant_id}).fetchone()
    print(f"  Active ESG KPI Definitions: {kpi_defs[0]}")
    
    # 5. Check ESG scores
    print("\n--- ESG SCORES ---")
    esg_scores = db.execute(text(
        "SELECT id, overall_score, environmental_score, social_score, governance_score, period FROM esg_scores "
        "WHERE workspace_id=:wid AND is_deleted=0 ORDER BY created_at DESC LIMIT 5"
    ), {"wid": workspace_id}).fetchall()
    if not esg_scores:
        print("  WARNING: No ESG scores found for workspace!")
    else:
        for r in esg_scores:
            print(f"  ID={r[0]} | overall={r[1]:.4f} | E={r[2]:.4f} | S={r[3]:.4f} | G={r[4]:.4f} | period={r[5]}")

    # 6. Check sustainability_conformance snapshots
    print("\n--- SUSTAINABILITY CONFORMANCE ---")
    susc = db.execute(text(
        "SELECT id, json_extract(simulation_metadata, '$.simulation_type'), "
        "json_extract(simulation_metadata, '$.conformance_score') "
        "FROM scenario_simulations WHERE analysis_id=:aid "
        "AND json_extract(simulation_metadata, '$.simulation_type')='sustainability_conformance' LIMIT 5"
    ), {"aid": analysis_id}).fetchall()
    if not susc:
        print("  WARNING: No sustainability_conformance snapshots!")
    else:
        for r in susc:
            print(f"  ID={r[0]} | type={r[1]} | score={r[2]}")

# 7. Check UserRoles (for benchmark)
print("\n--- USER ROLES ---")
user_roles = db.execute(text(
    "SELECT user_id, organization_id, role FROM user_roles LIMIT 5"
)).fetchall()
if not user_roles:
    print("  WARNING: No user roles found!")
else:
    for r in user_roles:
        print(f"  user_id={r[0]} | org_id={r[1]} | role={r[2]}")

# 8. Check Workspaces
print("\n--- WORKSPACES ---")
workspaces = db.execute(text(
    "SELECT id, name, organization_id FROM workspaces WHERE is_deleted=0 LIMIT 5"
)).fetchall()
if not workspaces:
    print("  WARNING: No workspaces found!")
else:
    for r in workspaces:
        print(f"  id={r[0]} | name={r[1]} | org_id={r[2]}")

db.close()
print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
