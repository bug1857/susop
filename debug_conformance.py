import os
import sys
import uuid

sys.path.append("/Users/rudrapratapsingh/Desktop/newpro/backend")
os.environ["USE_SQLITE"] = "true"

from app.core.database import SessionLocal
from app.models.models import User, Workspace, ProcessAnalysis
from app.services.object_conformance_service import ObjectConformanceService

db = SessionLocal()
ws = db.query(Workspace).first()
analysis = db.query(ProcessAnalysis).filter(ProcessAnalysis.workspace_id == ws.id).order_by(ProcessAnalysis.created_at.desc()).first()

print("Analysis ID:", analysis.id)

ocs = ObjectConformanceService(db)
latest = ocs.get_latest(analysis.id)
import pprint
pprint.pprint(latest)

print("\n--- Object Conformance Details ---")
summary = ocs.get_summary(analysis.id)
pprint.pprint(summary)
