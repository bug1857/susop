from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import time
import math
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, Workspace, UserRole
from app.services.hardware_service import HardwareService

import httpx

router = APIRouter(prefix="/benchmarking", tags=["benchmarking"])

class BenchmarkRequest(BaseModel):
    prompt: str
    workspace_id: UUID
    analysis_id: Optional[UUID] = None

class BenchmarkResult(BaseModel):
    model: str
    provider: str
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model_memory_gb: float
    hallucination_risk: str
    hallucination_risk_score: int
    contract_compliance_score: int
    response_text: str

def get_tenant_context(user_id: UUID, db: Session) -> UUID:
    role = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to any organization"
        )
    return role.organization_id


def _run_ollama_generate(model_name: str, prompt: str, timeout_seconds: int = 90) -> tuple[str, int]:
    """Run Ollama generate for a model with a timeout. Returns (response_text, latency_ms)."""
    OLLAMA_BASE_URL = "http://localhost:11434"
    start_time = time.monotonic()
    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 512,   # Cap tokens for speed
                    "temperature": 0.3
                }
            },
            timeout=timeout_seconds
        )
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        latency = int((time.monotonic() - start_time) * 1000)
        return text, latency
    except httpx.TimeoutException:
        latency = int((time.monotonic() - start_time) * 1000)
        return f"[Timeout after {timeout_seconds}s] Model did not respond in time.", latency
    except Exception as e:
        latency = int((time.monotonic() - start_time) * 1000)
        return f"[Error] {str(e)[:200]}", latency


def _compute_scores(model: str, response_text: str) -> tuple[int, int, str]:
    """Compute contract_compliance_score, hallucination_risk_score, risk_label."""
    required_sections = [
        "Executive Summary",
        "Root Cause",
        "Impact",
        "Recommend",
        "Improvement",
        "Confidence"
    ]
    resp_lower = response_text.lower()
    sections_found = sum(1 for sec in required_sections if sec.lower() in resp_lower)
    contract_score = 40 + (sections_found * 10)
    contract_score = min(100, contract_score)

    risk_score = 30
    model_lower = model.lower()
    if "1.5b" in model_lower:
        risk_score += 20
    elif "4b" in model_lower:
        risk_score += 10
    elif "8b" in model_lower:
        risk_score -= 5
    elif "12b" in model_lower or "14b" in model_lower:
        risk_score -= 10
    elif "70b" in model_lower:
        risk_score -= 15

    if "deepseek" in model_lower or "r1" in model_lower:
        risk_score -= 10
    if "vl" in model_lower:
        risk_score += 5  # VL models slightly higher risk for text tasks

    if contract_score >= 90:
        risk_score -= 10
    if len(response_text.strip()) < 50:
        risk_score += 25
    if "timeout" in response_text.lower() or "error" in response_text.lower()[:10]:
        risk_score += 30

    risk_score = max(5, min(95, risk_score))

    if risk_score > 60:
        risk_label = "High"
    elif risk_score > 30:
        risk_label = "Medium"
    else:
        risk_label = "Low"

    return contract_score, risk_score, risk_label


@router.post("/run", response_model=List[BenchmarkResult])
def run_benchmarks(
    payload: BenchmarkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resolved_tenant_id = get_tenant_context(current_user.id, db)

    # Context security validation
    ws = db.query(Workspace).filter(
        Workspace.id == payload.workspace_id,
        Workspace.organization_id == resolved_tenant_id
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # ── Dynamically fetch installed models from Ollama ─────────────────────────
    installed_names = HardwareService.get_installed_model_names()

    if not installed_names:
        raise HTTPException(
            status_code=503,
            detail="No Ollama models are installed. Please pull at least one model (e.g. `ollama pull qwen2.5:1.5b`) and retry."
        )

    results = []

    for model in installed_names:
        meta = HardwareService.get_model_metadata(model)
        memory = meta.get("size_gb", 4.0)

        # Run with a per-model timeout of 90 seconds
        response_text, latency_ms = _run_ollama_generate(model, payload.prompt, timeout_seconds=90)

        # Token accounting
        prompt_tokens = math.ceil(len(payload.prompt) / 4)
        completion_tokens = math.ceil(len(response_text) / 4)
        total_tokens = prompt_tokens + completion_tokens

        contract_score, risk_score, risk_label = _compute_scores(model, response_text)

        results.append(BenchmarkResult(
            model=model,
            provider="Ollama",
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model_memory_gb=memory,
            hallucination_risk=risk_label,
            hallucination_risk_score=risk_score,
            contract_compliance_score=contract_score,
            response_text=response_text
        ))

    return results


@router.get("/models", tags=["benchmarking"])
def list_available_models():
    """List all currently installed Ollama models available for benchmarking."""
    installed = HardwareService.get_installed_models()
    return {
        "available": len(installed) > 0,
        "models": installed
    }
