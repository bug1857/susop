import os
import sys
import uuid

sys.path.append("/Users/rudrapratapsingh/Desktop/newpro/backend")
os.environ["USE_SQLITE"] = "true"

from app.core.database import SessionLocal
from app.models.models import User, Workspace, ProcessAnalysis
from app.services.sustainability_digital_twin_service import SustainabilityDigitalTwinService

db = SessionLocal()
ws = db.query(Workspace).first()
analysis = db.query(ProcessAnalysis).filter(ProcessAnalysis.workspace_id == ws.id).order_by(ProcessAnalysis.created_at.desc()).first()

print("Analysis ID:", analysis.id)

from app.services.object_carbon_service import ObjectCarbonAttributionService
ocas = ObjectCarbonAttributionService(db)
objects = ocas.get_objects(analysis.id)
import pprint
pprint.pprint(objects)

# Done
