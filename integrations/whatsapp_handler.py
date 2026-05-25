import requests
import json
import os
from thefuzz import fuzz

CONFIG_FILE = "hedwig_config.json"


def _load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)



def setup_green_api(instance_id: str, api_token: str) -> dict:
    """Verify Green API keys and save them."""
    url = f"https://api.green-api.com/waInstance{instance_id}/getStateInstance/{api_token}"
    try:
        resp  = requests.get(url, timeout=10)
        state = resp.json().get("stateInstance", "")

        if state == "authorized":
            config = _load_config()
            config["instance_id"]      = instance_id
            config["api_token"]        = api_token
            config["trusted_contacts"] = config.get("trusted_contacts", {})
            _save_config(config)
            slots_left = 3 - len(config["trusted_contacts"])
            return {
                "success":   True,
                "message":   f"WhatsApp connected. Add up to {slots_left} trusted contact(s).",
                "slots_left": slots_left
            }

        if state == "notAuthorized":
            return {
                "success": False,
                "message": "Instance not authorized. Scan the QR code at app.green-api.com first."
            }

        return {"success": False, "message": f"Instance state: '{state}'. Link WhatsApp first."}

    except Exception as e:
        return {"success": False, "message": f"Connection error: {e}"}


def add_trusted_contact(name: str, phone: str) -> dict:
    config  = _load_config()
    trusted = config.get("trusted_contacts", {})

    if "instance_id" not in config:
        return {"success": False, "message": "Green API not set up yet."}

    if len(trusted) >= 3:
        names = ", ".join(trusted.keys())
        return {
            "success": False,
            "message": f"All 3 slots taken ({names}). Remove one to add another."
        }

    phone_clean               = phone.replace("+", "").replace(" ", "").replace("-", "")
    key                       = name.strip().lower()
    trusted[key]              = phone_clean
    config["trusted_contacts"] = trusted
    _save_config(config)

    slots_left = 3 - len(trusted)
    return {
        "success":        True,
        "message":        f"Added '{name}'. {slots_left} slot(s) remaining.",
        "slots_left":     slots_left,
        "trusted_contacts": trusted
    }


def remove_trusted_contact(name: str) -> dict:
    config  = _load_config()
    trusted = config.get("trusted_contacts", {})
    key     = name.strip().lower()

    if key not in trusted:
        return {"success": False, "message": f"'{name}' not in trusted contacts."}

    del trusted[key]
    config["trusted_contacts"] = trusted
    _save_config(config)

    return {
        "success": True,
        "message": f"Removed '{name}'. {3 - len(trusted)} slot(s) now free.",
        "trusted_contacts": trusted
    }


def list_trusted_contacts() -> dict:
    config  = _load_config()
    trusted = config.get("trusted_contacts", {})
    return {
        "success":    True,
        "contacts":   trusted,
        "slots_used": len(trusted),
        "slots_left": 3 - len(trusted)
    }


def resolve_contact(spoken_name: str) -> dict:

    config  = _load_config()
    trusted = config.get("trusted_contacts", {})

    if not trusted:
        return {
            "found":   False,
            "message": "No trusted contacts set up. Add up to 3 in settings first."
        }

    spoken_lower = spoken_name.strip().lower()
    best_score   = -1
    best_name    = None
    best_phone   = None

    for saved_name, phone in trusted.items():
        score = fuzz.token_set_ratio(spoken_lower, saved_name)
        print(f"  [Contact Fuzzy] '{spoken_name}' vs '{saved_name}' → {score}")

        if score > best_score:
            best_score = score
            best_name  = saved_name
            best_phone = phone
    if best_score >= 50:
        return {
            "found":        True,
            "matched_name": best_name,
            "phone":        best_phone,
            "score":        best_score
        }

    trusted_names = ", ".join(trusted.keys())
    return {
        "found":   False,
        "message": (
            f"Couldn't match '{spoken_name}' to any trusted contact. "
            f"Your trusted contacts are: {trusted_names}."
        )
    }


def send_whatsapp_message(phone: str, message: str, matched_name: str = "") -> dict:
    
    config = _load_config()

    if "instance_id" not in config:
        return {
            "success": False,
            "message": "WhatsApp not set up. Add Green API keys in settings."
        }

    instance_id = config["instance_id"]
    api_token   = config["api_token"]
    chat_id     = f"{phone}@c.us"
    url         = f"https://api.green-api.com/waInstance{instance_id}/sendMessage/{api_token}"

    try:
        resp = requests.post(url, json={"chatId": chat_id, "message": message}, timeout=10)
        data = resp.json()

        if data.get("idMessage"):
            name = matched_name or phone
            return {"success": True, "message": f"Message sent to {name}."}

        if "quotaExceeded" in str(data):
            return {
                "success": False,
                "message": "Monthly quota exceeded. Resets on the 1st of next month."
            }

        return {"success": False, "message": f"Green API error: {data}"}

    except requests.Timeout:
        return {"success": False, "message": "Request timed out."}
    except Exception as e:
        return {"success": False, "message": f"Error: {e}"}


class WhatsappHandler:
    def find_contact(self, spoken_name: str) -> str | None:
        result = resolve_contact(spoken_name)
        return result.get("phone") if result["found"] else None