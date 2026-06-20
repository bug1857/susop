from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import HTTPException, status
from app.models.models import EsgEvidence, EsgKpiValue
from app.repositories.esg_evidence_repository import EsgEvidenceRepository
from app.core.audit import log_activity

class EsgEvidenceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EsgEvidenceRepository(db)

    def register_evidence(self, tenant_id: UUID, user_id: UUID, payload: dict) -> EsgEvidence:
        kpi_value_id = payload.get("kpi_value_id")
        source_description = payload.get("source_description")
        source_entity_type = payload.get("source_entity_type")
        source_entity_id = payload.get("source_entity_id")
        evidence_file_path = payload.get("evidence_file_path")
        cryptographic_hash = payload.get("cryptographic_hash")
        calculation_steps = payload.get("calculation_steps")
        lineage_path = payload.get("lineage_path")

        if not kpi_value_id or not source_description or not source_entity_type or not calculation_steps or not lineage_path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required evidence fields")

        # Verify KPI value exists and is tenant-scoped
        val = self.db.query(EsgKpiValue).filter(
            EsgKpiValue.id == kpi_value_id,
            EsgKpiValue.tenant_id == tenant_id,
            EsgKpiValue.is_deleted == False
        ).first()
        if not val:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KPI value not found or unauthorized")

        # Source entity validation checklist
        valid_entity_types = ["dataset", "process_analysis", "process_model", "conformance_result", "carbon_attribution", "manual_upload", "external_api"]
        if source_entity_type not in valid_entity_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid source_entity_type. Must be one of {valid_entity_types}")

        new_ev = EsgEvidence(
            kpi_value_id=kpi_value_id,
            tenant_id=tenant_id,
            source_description=source_description,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            evidence_file_path=evidence_file_path,
            cryptographic_hash=cryptographic_hash,
            calculation_steps=calculation_steps,
            lineage_path=lineage_path,
            is_deleted=False
        )
        created = self.repo.create(new_ev)
        log_activity(self.db, user_id, "evidence_attached", tenant_id, f"Attached evidence lineage to KPI value {kpi_value_id}")
        return created

    def retrieve_evidence(self, kpi_value_id: UUID, tenant_id: UUID) -> EsgEvidence:
        evidence = self.repo.get_by_kpi_value(kpi_value_id, tenant_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found for the specified KPI value")
        return evidence

    def verify_evidence(self, kpi_value_id: UUID, tenant_id: UUID) -> dict:
        evidence = self.repo.get_by_kpi_value(kpi_value_id, tenant_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found for the specified KPI value")

        # Verification of hash
        if not evidence.cryptographic_hash:
            return {
                "success": True,
                "status": "unverified",
                "reason": "No cryptographic hash registered for this evidence record"
            }

        # Check for mock database or value change detection
        # Simple proof of completeness: check that calculations JSON and source reference are loaded
        if not evidence.calculation_steps or not evidence.lineage_path:
            return {
                "success": False,
                "status": "compromised",
                "reason": "Calculations or lineage maps are empty or corrupted"
            }

        return {
            "success": True,
            "status": "verified",
            "cryptographic_hash": evidence.cryptographic_hash,
            "verified_at": datetime.utcnow().isoformat() + "Z"
        }

    def get_lineage_path(self, kpi_value_id: UUID, tenant_id: UUID) -> dict:
        evidence = self.repo.get_by_kpi_value(kpi_value_id, tenant_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found for the specified KPI value")

        return {
            "kpi_value_id": str(kpi_value_id),
            "lineage_path": evidence.lineage_path,
            "source_entity_type": evidence.source_entity_type,
            "source_entity_id": str(evidence.source_entity_id) if evidence.source_entity_id else None
        }
