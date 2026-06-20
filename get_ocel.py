import os
import sys
import uuid
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import SessionLocal
from app.models.models import ObjectCentricEventLog

db = SessionLocal()
analysis_id = "aa639bae-06c6-4a2c-ab17-b38bf8b07048"
ocel = db.query(ObjectCentricEventLog).filter(ObjectCentricEventLog.analysis_id == uuid.UUID(analysis_id)).first()
if ocel:
    objs = json.loads(ocel.objects_json)
    for obj in objs:
        obj_type = obj.get("object_type")
        events = sorted(obj.get("events", []), key=lambda e: e["timestamp"])
        activities = [e["activity"] for e in events]
        print(f"Type: {obj_type}, ID: {obj.get('object_id')}, Events: {activities}")
