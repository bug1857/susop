import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import SessionLocal
from app.models.models import ProcessAnalysis

db = SessionLocal()
analysis = db.query(ProcessAnalysis).filter(
    ProcessAnalysis.id == "4127d16c-2f76-4cea-88db-b5d2b9849fce"
).first()
if analysis:
    print(f"Status: {analysis.status}")
