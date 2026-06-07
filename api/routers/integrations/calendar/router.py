from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_current_user
from api.routers.integrations.calendar.schemas import CalendarCredentialsPayload
from integrations.calendar_tools import disconnect, run_oauth_flow, save_credentials
from storage.queries import upsert_integration
from storage.secrets import make_secret_ref


router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/connect")
def connect_calendar(payload: CalendarCredentialsPayload, current_user=Depends(get_current_user)):
    user_id = current_user["id"]

    try:
        save_credentials(user_id, payload.credentials_json)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    result = run_oauth_flow(user_id)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    upsert_integration(
        user_id,
        provider="google_calendar",
        status="connected",
        secret_ref=make_secret_ref(user_id, "google_calendar", "token"),
        masked_label="Google Calendar",
        metadata={"credentials_secret_ref": make_secret_ref(user_id, "google_calendar", "credentials")},
    )
    return {"success": True, "provider": "google_calendar", "connected": True}


@router.delete("")
async def disconnect_calendar(current_user=Depends(get_current_user)):
    disconnect(current_user["id"])
    upsert_integration(
        current_user["id"],
        provider="google_calendar",
        status="disconnected",
        secret_ref=None,
        masked_label=None,
        metadata={},
    )
    return {"success": True}
