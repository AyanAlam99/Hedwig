from integrations.spotify_handler import play_on_spotify, pause_spotify, resume_spotify
from integrations.whatsapp_handler import send_whatsapp_message, resolve_contact
from integrations.calendar_tools import create_event
from integrations.open_app import open_app, open_url_in_browser, WEBSITE_MAP

def handle_spotify(params: dict) -> dict:
    target    = params.get("target", "")
    content   = params.get("content", "")
    track_uri = params.get("track_uri")
    return play_on_spotify(target, content, track_uri=track_uri)

def handle_whatsapp(params: dict) -> dict:
    matched_name   = params.get("target", "").strip()
    message        = params.get("content", "").strip()
    resolved_phone = params.get("resolved_phone", "").strip()

    if not message:
        return {"success": False, "message": "No message to send."}

    if not resolved_phone:
        result = resolve_contact(matched_name)
        if not result["found"]:
            return {"success": False, "message": result["message"]}
        resolved_phone = result["phone"]
        matched_name   = result["matched_name"]

    return send_whatsapp_message(
        phone=resolved_phone,
        message=message,
        matched_name=matched_name
    )

def handle_calendar(params: dict) -> dict:
    title    = params.get('target') or params.get('content') or "Voice Assistant Meeting"
    date_str = params.get('date')
    time_str = params.get('time', "")

    if not date_str:
        return {"success": False, "message": "Missing date."}

    return create_event(title=title, date=date_str, time_str=time_str)

def handle_open_app(params: dict, platform: str) -> dict:
    target   = params.get("target", "").strip().lower()
    content  = params.get("content", "").strip().lower()
    app_name = target or content or platform

    if not app_name:
        return {"success": False, "message": "What would you like me to open?"}

    if app_name in WEBSITE_MAP:
        if platform in ["firefox", "chrome", "edge", "brave"]:
            return open_url_in_browser(WEBSITE_MAP[app_name], browser=platform)
        return open_url_in_browser(WEBSITE_MAP[app_name])

    return open_app(app_name)

def handle_youtube(params: dict) -> dict:
    import urllib.parse
    query = (params.get("target") or params.get("content", "")).strip()
    if not query:
        return {"success": False, "message": "No query provided."}
    encoded = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    # Open it too
    open_url_in_browser(url)
    return {"success": True, "action": "open_url", "url": url, "message": f"Opening YouTube for {query}."}