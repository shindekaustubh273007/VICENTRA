from fastapi import APIRouter
from app.services.stream_manager import stream_manager

router = APIRouter()

@router.get("")
def get_global_health():
    healths = stream_manager.get_all_health()
    return {
        "status": "UP",
        "active_streams": len([h for h in healths if h["status"] == "ONLINE"]),
        "total_managed": len(healths),
        "streams": healths
    }
