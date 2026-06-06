import requests
from thefuzz import fuzz

from storage.crypto import normalize_phone
from storage.queries import get_active_user_id, get_integration, list_trusted_contact_numbers
from storage.secrets import get_secret


def _load_wa_creds(user_id: int | None = None) -> tuple[str, str] | tuple[None, None]:
    """Returns (instance_id, api_token) from keyring, or (None, None) if not set up."""
    uid = user_id if user_id is not None else get_active_user_id()
    if uid is None:
        return None, None

    item = get_integration(uid, "whatsapp")
    if not item or item["status"] != "connected":
        return None, None

    meta = item.get("metadata", {})
    instance_ref = meta.get("instance_secret_ref")
    token_ref = item.get("secret_ref")

    instance_id = get_secret(instance_ref) if instance_ref else None
    api_token = get_secret(token_ref) if token_ref else None

    return instance_id, api_token


def resolve_contact(spoken_name: str, user_id: int | None = None) -> dict:
    uid = user_id if user_id is not None else get_active_user_id()
    if uid is None:
        return {"found": False, "message": "No user account found."}

    contacts = list_trusted_contact_numbers(uid, "whatsapp")

    if not contacts:
        return {
            "found": False,
            "message": "No trusted contacts set up. Add up to 3 in settings first.",
        }

    spoken_lower = spoken_name.strip().lower()
    best_score = -1
    best_name = None
    best_phone = None

    for saved_name, phone in contacts.items():
        score = fuzz.token_set_ratio(spoken_lower, saved_name)
        print(f"  [Contact Fuzzy] '{spoken_name}' vs '{saved_name}' → {score}")
        if score > best_score:
            best_score = score
            best_name = saved_name
            best_phone = phone

    if best_score >= 50:
        return {"found": True, "matched_name": best_name, "phone": best_phone, "score": best_score}

    trusted_names = ", ".join(contacts.keys())
    return {
        "found": False,
        "message": (
            f"Couldn't match '{spoken_name}' to any trusted contact. "
            f"Your trusted contacts are: {trusted_names}."
        ),
    }


def send_whatsapp_message(phone: str, message: str, matched_name: str = "", user_id: int | None = None) -> dict:
    instance_id, api_token = _load_wa_creds(user_id)

    if not instance_id or not api_token:
        return {"success": False, "message": "WhatsApp not set up. Connect Green API in settings."}

    chat_id = f"{normalize_phone(phone)}@c.us"
    url = f"https://api.green-api.com/waInstance{instance_id}/sendMessage/{api_token}"

    try:
        resp = requests.post(url, json={"chatId": chat_id, "message": message}, timeout=10)
        data = resp.json()

        if data.get("idMessage"):
            name = matched_name or phone
            return {"success": True, "message": f"Message sent to {name}."}

        if "quotaExceeded" in str(data):
            return {"success": False, "message": "Monthly quota exceeded. Resets on the 1st of next month."}

        return {"success": False, "message": f"Green API error: {data}"}

    except requests.Timeout:
        return {"success": False, "message": "Request timed out."}
    except Exception as e:
        return {"success": False, "message": f"Error: {e}"}


class WhatsappHandler:
    def find_contact(self, spoken_name: str, user_id: int | None = None) -> str | None:
        result = resolve_contact(spoken_name, user_id=user_id)
        return result.get("phone") if result["found"] else None
