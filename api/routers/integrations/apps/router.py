from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from api.routers.integrations.apps.schemas import AppPayload, BrowserPayload
from integrations.open_app import (
    auto_detect,
    list_apps,
    register_app,
    remove_app,
    set_default_browser,
)


router = APIRouter(prefix="/apps", tags=["apps"])


@router.get("")
async def get_apps(current_user=Depends(get_current_user)):
    return list_apps(current_user["id"])


@router.post("")
async def add_app(payload: AppPayload, current_user=Depends(get_current_user)):
    return register_app(current_user["id"], payload.name, payload.path)


@router.delete("")
async def delete_app(payload: AppPayload, current_user=Depends(get_current_user)):
    return remove_app(current_user["id"], payload.name)


@router.get("/detect/{app_name}")
async def detect_app(app_name: str, current_user=Depends(get_current_user)):
    return auto_detect(app_name)


@router.post("/default-browser")
async def default_browser(payload: BrowserPayload, current_user=Depends(get_current_user)):
    return set_default_browser(current_user["id"], payload.name)
