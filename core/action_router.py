from integrations.spotify_handler import play_on_spotify , pause_spotify  , resume_spotify 
from core.handler import handle_open_app , handle_calendar , handle_spotify , handle_whatsapp 
import os 
from dotenv import load_dotenv


load_dotenv()

GREEN_API_KEY = os.getenv("GREEN_API_KEY")
GREEN_API_INSTACE = os.getenv("GREEN_API_INSTANCE")

class ActionRouter : 


    def generate_confirmation_prompt(self,intent_data: dict) -> str:
        intent   = intent_data.get("intent", "unknown")
        platform = intent_data.get("platform", "unknown")
        params   = intent_data.get("parameters", {}) or {}

        target   = params.get("target", "")   or ""
        content  = params.get("content", "")  or ""
        date     = params.get("date", "")  or ""
        time     = params.get("time", "")  or ""
        modifier = params.get("action_modifier", "") or ""

        if intent == "schedule_meeting" or platform == "calendar":
            title = target or content or "a meeting"
            date_str = date or "an unspecified date"
            time_str = time or "an unspecified time"
            return (
                f"So you want me to schedule '{title}' "
                f"on {date_str} at {time_str}. Shall I go ahead?"
            )
        
        elif intent == "send_message" and platform == "whatsapp":
            contact = target or "someone"
            message = content or "a message"
            return (
                f"You want me to send '{message}' "
                f"to {contact} on WhatsApp. Confirm?"
            )

        elif intent in ["play music","play track","play_media"]:
            song = content 
            artist = target if target and target!=content  else ""
            if modifier:
                return f"You want me to play '{song}' on Spotify by  {artist}. Shall I?"
            return f"You want me to play '{song}' on Spotify by {artist}. Shall I?"
        
        elif intent == "open_app":
            print("jinglanfsfs")
            app_name = params.get("target") or params.get("content") or "something"
            platform = params.get("platform", "")
            if not app_name:
                app_name = platform 
            if platform in ["brave", "chrome", "firefox", "edge"]:
                return f"You want me to open {app_name} in {platform}. Shall I?"
            return f"You want me to open {app_name}. Shall I?"
        
        elif intent == "search":
            query    = content or target or "something"
            platform_name = platform if platform not in ("unknown", "general") else "Google"
            return f"You want me to search for '{query}' on {platform_name}. Confirm?"
        else:
            
            return f"didnt get anything , youre asked app name :{app_name} and platform : {platform} "

    def execute(self, intent_data : dict)  :
        if not intent_data : 
            return f"no intent data found"
        
        intent = intent_data.get("intent")
        platform = intent_data.get("platform")
        params = intent_data.get("parameters", {})

        print(f"Router Routing command: {intent} -> {platform}")

        if intent == "schedule_meeting" or platform == "calendar":
            result = handle_calendar(params)
            return result or {"message": "Event created."}

        elif intent in ["play music", "play track", "play_media"] :
            result = handle_spotify(params)
            return result or {"message": "Playing now."}
        
        elif intent in ["pause", "pause_music", "pause_media"]:
            result = pause_spotify()
            print(f"  [Spotify] Pause triggered: {result['message']}")
            return result

        elif intent in ["resume", "resume_music", "resume_media"]:
            result = resume_spotify()
            print(f"  [Spotify] Resume triggered: {result['message']}")
            return result

        elif intent == "send_message" or platform == "whatsapp":
            result =handle_whatsapp(params)
            return result or {"message": "Message sent."}
        
        elif intent == "open_app":
            print(f"In the exection method and the platform is {platform}")
            result = handle_open_app(params, platform)
            return result or {"message": "Done."}

        
        
