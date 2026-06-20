from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import AiCopilotResponse

class AiCopilotRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, response: AiCopilotResponse) -> AiCopilotResponse:
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        return response

    def latest_response(
        self, tenant_id: UUID, workspace_id: UUID, project_id: UUID, entity_id: UUID, request_type: str
    ) -> Optional[AiCopilotResponse]:
        return self.db.query(AiCopilotResponse).filter(
            AiCopilotResponse.tenant_id == tenant_id,
            AiCopilotResponse.workspace_id == workspace_id,
            AiCopilotResponse.project_id == project_id,
            AiCopilotResponse.entity_id == entity_id,
            AiCopilotResponse.request_type == request_type,
            AiCopilotResponse.is_deleted == False
        ).order_by(AiCopilotResponse.created_at.desc()).first()

    def list_responses(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        request_type: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[AiCopilotResponse]:
        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        query = self.db.query(AiCopilotResponse).filter(
            AiCopilotResponse.tenant_id == tenant_id,
            AiCopilotResponse.is_deleted == False
        )

        if workspace_id:
            query = query.filter(AiCopilotResponse.workspace_id == workspace_id)
        if project_id:
            query = query.filter(AiCopilotResponse.project_id == project_id)
        if analysis_id:
            query = query.filter(AiCopilotResponse.analysis_id == analysis_id)
        if request_type:
            query = query.filter(AiCopilotResponse.request_type == request_type)
        if provider:
            query = query.filter(AiCopilotResponse.provider == provider)

        allowed_sort_fields = {"created_at", "provider", "request_type"}
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        sort_col = getattr(AiCopilotResponse, sort_by)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        return query.limit(limit).offset(offset).all()

    def count_responses(
        self,
        tenant_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        analysis_id: Optional[UUID] = None,
        request_type: Optional[str] = None,
        provider: Optional[str] = None
    ) -> int:
        query = self.db.query(AiCopilotResponse).filter(
            AiCopilotResponse.tenant_id == tenant_id,
            AiCopilotResponse.is_deleted == False
        )

        if workspace_id:
            query = query.filter(AiCopilotResponse.workspace_id == workspace_id)
        if project_id:
            query = query.filter(AiCopilotResponse.project_id == project_id)
        if analysis_id:
            query = query.filter(AiCopilotResponse.analysis_id == analysis_id)
        if request_type:
            query = query.filter(AiCopilotResponse.request_type == request_type)
        if provider:
            query = query.filter(AiCopilotResponse.provider == provider)

        return query.count()
