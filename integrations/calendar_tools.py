import json
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from storage.queries import get_active_user_id
from storage.secrets import delete_secret, get_secret, make_secret_ref, set_secret

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = "Asia/Kolkata"


def _creds_ref(user_id: int) -> str:
    return make_secret_ref(user_id, "google_calendar", "credentials")


def _token_ref(user_id: int) -> str:
    return make_secret_ref(user_id, "google_calendar", "token")


def _resolve_user_id(user_id: int | None) -> int | None:
    return user_id if user_id is not None else get_active_user_id()


def save_credentials(user_id: int, credentials_json: str):
    try:
        data = json.loads(credentials_json)
    except json.JSONDecodeError as exc:
        raise ValueError("credentials.json is not valid JSON.") from exc

    if "installed" not in data and "web" not in data:
        raise ValueError(
            "credentials.json must be an OAuth client (expected an 'installed' Desktop-app client)."
        )

    set_secret(_creds_ref(user_id), credentials_json)


def run_oauth_flow(user_id: int) -> dict:
    """
    opens a browser on the PC for the user to grant calendar access.
    Stores the resulting token in keyring. Blocks until the user finishes consent.
    """
    creds_json = get_secret(_creds_ref(user_id))
    if not creds_json:
        return {"success": False, "message": "Upload your credentials.json before authorizing."}

    try:
        client_config = json.loads(creds_json)
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=0)
    except Exception as e:
        return {"success": False, "message": f"Authorization failed: {e}"}

    set_secret(_token_ref(user_id), creds.to_json())
    return {"success": True, "message": "Google Calendar connected."}


def disconnect(user_id: int):
    delete_secret(_creds_ref(user_id))
    delete_secret(_token_ref(user_id))


def is_connected(user_id: int) -> bool:
    return bool(get_secret(_token_ref(user_id)))


def _get_service(user_id: int):
    creds_json = get_secret(_creds_ref(user_id))
    token_json = get_secret(_token_ref(user_id))

    if not creds_json:
        raise RuntimeError("Calendar not connected: no credentials uploaded.")
    if not token_json:
        raise RuntimeError("Calendar not connected: not authorized yet.")

    creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            print(" Calendar - Refreshing token...")
            creds.refresh(Request())
            # Persist the refreshed token back to keyring
            set_secret(_token_ref(user_id), creds.to_json())
        else:
            raise RuntimeError("Calendar authorization expired. Reconnect in settings.")

    return build("calendar", "v3", credentials=creds)


def create_event(
    title: str,
    date: str,
    time_str: str = "15:00",
    duration_minutes: int = 60,
    description: str = "",
    attendees: list[str] = None,
    user_id: int = None,
) -> dict:
    if not title:
        return {"success": False, "message": "Event title is required"}
    if not date:
        return {"success": False, "message": "Date is required"}
    if not time_str:
        time_str = "15:00"

    uid = _resolve_user_id(user_id)
    if uid is None:
        return {"success": False, "message": "No user account found."}

    try:
        start_dt = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
    except ValueError:
        return {
            "success": False,
            "message": f"Invalid date/time format: {date} {time_str}. Expected YYYY-MM-DD and HH:MM.",
        }

    event_body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 10},
                {"method": "email", "minutes": 30},
            ],
        },
    }

    if attendees:
        event_body["attendees"] = [{"email": e} for e in attendees]

    try:
        service = _get_service(uid)
        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            sendUpdates="all" if attendees else "none",
        ).execute()

        spoken_time = start_dt.strftime("%B %d at %I:%M %p").lstrip("0")

        return {
            "success": True,
            "event_id": event.get("id"),
            "link": event.get("htmlLink"),
            "message": f"{title} created for {spoken_time}.",
        }

    except Exception as e:
        error = str(e)
        print(f"  Calendar API error: {error}")
        return {"success": False, "message": f"Couldn't create the event. Error: {error}"}
