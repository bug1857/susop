import os
import sys
from uuid import UUID

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import SessionLocal
from app.models.models import ProcessAnalysis, Workspace

db = SessionLocal()
analyses = db.query(ProcessAnalysis).order_by(ProcessAnalysis.created_at.desc()).limit(3).all()
for a in analyses:
    print(f"ID: {a.id}, Status: {a.status}, Created: {a.created_at}")
