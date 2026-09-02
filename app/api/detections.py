"""
Phase 2 — API endpoints for AI engine status.

GET /api/ai/status — global inference status & metrics
"""

from fastapi import APIRouter
from app.services.inference_manager import inference_manager
from app.models.schemas import InferenceStatusResponse

# ── Global AI router (mounted under /api/ai) ─────────────────────────
ai_router = APIRouter()

@ai_router.get("/status", response_model=InferenceStatusResponse)
def get_ai_status():
    """Return the overall AI inference engine status and per-camera metrics."""
    return inference_manager.get_all_status()

