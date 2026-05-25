from fastapi import APIRouter
from core.state import app_logs

router = APIRouter(prefix="/api", tags=["logs"])

@router.get("/logs")
async def get_logs():
    return {"logs": app_logs}