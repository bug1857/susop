import os
import sys
import uuid
import json

sys.path.append("/Users/rudrapratapsingh/Desktop/newpro/backend")
os.environ["USE_SQLITE"] = "true"

from app.core.database import SessionLocal
from app.models.models import User, Workspace, Project, ProcessAnalysis, AiInsight
from app.services.ai_copilot_service import AiCopilotService

db = SessionLocal()
user = db.query(User).first()
ws = db.query(Workspace).first()
analysis = db.query(ProcessAnalysis).filter(ProcessAnalysis.workspace_id == ws.id).order_by(ProcessAnalysis.created_at.desc()).first()
insight = db.query(AiInsight).filter(AiInsight.analysis_id == analysis.id).first()

print(f"User: {user.email}")
print(f"Workspace ID: {ws.id}")
print(f"Project ID: {analysis.project_id}")
print(f"Analysis ID: {analysis.id}")
print(f"Insight ID: {insight.id if insight else None}")

service = AiCopilotService(db)

# Let's try calling generate_response directly
try:
    res = service.generate_response(
        tenant_id=ws.organization_id,
        workspace_id=ws.id,
        project_id=analysis.project_id,
        analysis_id=analysis.id,
        entity_type="INSIGHT",
        entity_id=insight.id if insight else uuid.uuid4(),
        request_type="EXECUTIVE_BRIEF",
        provider="OLLAMA",
        user_id=user.id,
        user_query="What are total emissions?"
    )
    print("Success! Response:")
    print("Response text:", res.response_text)
    print("Metadata:", res.response_metadata)
except Exception as e:
    import traceback
    print("Failed:")
    traceback.print_exc()
