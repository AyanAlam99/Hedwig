import requests
from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_current_user
from api.routers.integrations.whatsapp.schemas import (
    ContactPayload,
    RemoveContactPayload,
    WhatsAppConnectPayload,
)
from storage.queries import (
    add_trusted_contact,
    get_integration,
    list_trusted_contacts,
    remove_trusted_contact,
    upsert_integration,
)
from storage.secrets import (
    SecretStorageUnavailable,
    delete_secret,
    make_secret_ref,
    set_secret,
)
from storage.security import mask_identifier


router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/connect")
async def connect_whatsapp(payload: WhatsAppConnectPayload, current_user=Depends(get_current_user)):
    instance_id = payload.instance_id.strip()
    api_token = payload.api_token.strip()
    if not instance_id or not api_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instance ID and API token are required.",
        )

    url = f"https://api.green-api.com/waInstance{instance_id}/getStateInstance/{api_token}"
    try:
        resp = requests.get(url, timeout=10)
        state = resp.json().get("stateInstance", "")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not validate Green API credentials.",
        )

    if state == "notAuthorized":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instance not authorized. Scan the WhatsApp QR code first.",
        )
    if state != "authorized":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Green API instance state is '{state or 'unknown'}'.",
        )

    token_ref = make_secret_ref(current_user["id"], "whatsapp", "api_token")
    instance_ref = make_secret_ref(current_user["id"], "whatsapp", "instance_id")
    try:
        set_secret(token_ref, api_token)
        set_secret(instance_ref, instance_id)
    except SecretStorageUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception:
        delete_secret(token_ref)
        delete_secret(instance_ref)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not save credentials to secure secret storage.",
        )

    upsert_integration(
        current_user["id"],
        provider="whatsapp",
        status="connected",
        secret_ref=token_ref,
        masked_label=mask_identifier(instance_id),
        metadata={
            "api": "green_api",
            "instance_secret_ref": instance_ref,
        },
    )

    return {
        "success": True,
        "provider": "whatsapp",
        "connected": True,
        "masked_label": mask_identifier(instance_id),
    }


@router.delete("")
async def disconnect_whatsapp(current_user=Depends(get_current_user)):
    item = get_integration(current_user["id"], "whatsapp")
    if item:
        if item["secret_ref"]:
            delete_secret(item["secret_ref"])
        instance_ref = item["metadata"].get("instance_secret_ref")
        if instance_ref:
            delete_secret(instance_ref)

    upsert_integration(
        current_user["id"],
        provider="whatsapp",
        status="disconnected",
        secret_ref=None,
        masked_label=None,
        metadata={},
    )
    return {"success": True}


@router.get("/contacts")
async def get_whatsapp_contacts(current_user=Depends(get_current_user)):
    contacts = list_trusted_contacts(current_user["id"], "whatsapp")
    return {
        "success": True,
        "contacts": contacts,
        "slots_used": len(contacts),
        "slots_left": max(0, 3 - len(contacts)),
    }


@router.post("/contacts")
async def add_whatsapp_contact(payload: ContactPayload, current_user=Depends(get_current_user)):
    contacts = list_trusted_contacts(current_user["id"], "whatsapp")
    name = payload.name.strip().lower()
    if name not in contacts and len(contacts) >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All 3 trusted contact slots are already used.",
        )

    add_trusted_contact(current_user["id"], "whatsapp", payload.name, payload.phone)
    contacts = list_trusted_contacts(current_user["id"], "whatsapp")
    return {
        "success": True,
        "contacts": contacts,
        "slots_used": len(contacts),
        "slots_left": max(0, 3 - len(contacts)),
    }


@router.delete("/contacts")
async def delete_whatsapp_contact(payload: RemoveContactPayload, current_user=Depends(get_current_user)):
    remove_trusted_contact(current_user["id"], "whatsapp", payload.name)
    contacts = list_trusted_contacts(current_user["id"], "whatsapp")
    return {
        "success": True,
        "contacts": contacts,
        "slots_used": len(contacts),
        "slots_left": max(0, 3 - len(contacts)),
    }
