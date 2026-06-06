from integrations.spotify_handler import pause_spotify, resume_spotify
from core.handler import handle_open_app, handle_calendar, handle_spotify, handle_whatsapp


class ActionRouter:

    def generate_confirmation_prompt(self, intent_data: dict) -> str:
        intent   = intent_data.get("intent", "unknown")
        platform = intent_data.get("platform", "unknown")
        params   = intent_data.get("parameters", {}) or {}

        target  = params.get("target", "")  or ""
        content = params.get("content", "") or ""
        date    = params.get("date", "")    or ""
        time    = params.get("time", "")    or ""

        if intent == "schedule_meeting" or platform == "calendar":
            title    = target or content or "a meeting"
            date_str = date or "an unspecified date"
            time_str = time or "an unspecified time"
            return f"So you want me to schedule '{title}' on {date_str} at {time_str}. Shall I go ahead?"

        elif intent == "send_message" or platform == "whatsapp":
            contact = target or "someone"
            message = content or "a message"
            return f"You want me to send '{message}' to {contact} on WhatsApp. Confirm?"

        elif intent == "play_media":
            artist = target if target and target != content else ""
            return f"You want me to play '{content}' on Spotify by {artist}. Shall I?"

        elif intent == "open_app":
            app_name = target or content or platform or "something"
            if platform in ("brave", "chrome", "firefox", "edge"):
                return f"You want me to open {app_name} in {platform}. Shall I?"
            return f"You want me to open {app_name}. Shall I?"

        elif intent == "search":
            query         = content or target or "something"
            platform_name = platform if platform not in ("unknown", "general") else "Google"
            return f"You want me to search for '{query}' on {platform_name}. Confirm?"

        return "I'm not sure what you want. Could you repeat that?"

    def execute(self, intent_data: dict):
        if not intent_data:
            return {"message": "No intent data found."}

        intent   = intent_data.get("intent")
        platform = intent_data.get("platform")
        params   = intent_data.get("parameters", {})

        print(f"Router Routing command: {intent} -> {platform}")

        if intent == "schedule_meeting" or platform == "calendar":
            return handle_calendar(params) or {"message": "Event created."}

        elif intent == "play_media":
            return handle_spotify(params) or {"message": "Playing now."}

        elif intent == "pause":
            return pause_spotify()

        elif intent == "resume":
            return resume_spotify()

        elif intent == "send_message" or platform == "whatsapp":
            return handle_whatsapp(params) or {"message": "Message sent."}

        elif intent == "open_app":
            return handle_open_app(params, platform) or {"message": "Done."}

        return {"message": "I didn't know how to handle that."}
