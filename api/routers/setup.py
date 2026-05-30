from fastapi import APIRouter
from pydantic import BaseModel
from integrations.whatsapp_handler import (
    setup_green_api, add_trusted_contact, 
    remove_trusted_contact, list_trusted_contacts, _load_config
)

router = APIRouter(prefix="/api/setup", tags=["setup"])


class GreenAPIKeys(BaseModel):
    instance_id: str
    api_token: str

class ContactPayload(BaseModel):
    name: str
    phone: str   

class RemovePayload(BaseModel):
    name: str

@router.get("/status")
async def setup_status():
    config = _load_config()
    trusted = config.get("trusted_contacts", {})
    return {
        "whatsapp_connected": "instance_id" in config and "api_token" in config,
        "trusted_contacts": trusted,
        "slots_used": len(trusted),
        "slots_left": 3 - len(trusted),
        "onboarding_complete": "instance_id" in config,
    }

@router.post("/whatsapp")
async def connect_whatsapp(keys: GreenAPIKeys):
    return setup_green_api(keys.instance_id, keys.api_token)


@router.post("/api/setup/trusted-contact")
async def add_contact(payload: ContactPayload):
    """Step 2 — lock a trusted contact slot (max 3)."""
    result = add_trusted_contact(payload.name, payload.phone)
    return result
 
@router.delete("/api/setup/trusted-contact")
async def remove_contact(payload: RemovePayload):
    result = remove_trusted_contact(payload.name)
    return result
 
@router.get("/api/setup/trusted-contacts")
async def get_contacts():
    return list_trusted_contacts()
 