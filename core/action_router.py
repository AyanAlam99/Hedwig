import json
from datetime import datetime
import urllib.parse
from integrations.calendar_tools import create_event 
from integrations.spotify_handler import play_on_spotify , pause_spotify  , resume_spotify 
from audio.speech_to_text import NLUParser ,SpeechToText
from integrations.whatsapp_handler import WhatsappHandler
import requests,os 
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
        
        elif platform == "youtube":
            query = content or target or "something"
            if modifier:
                return f"You want me to search '{query}' on YouTube — {modifier}. Correct?"
            return f"You want me to open YouTube and search for '{query}'. Correct?"

        elif intent in ["play music","play track","play_media"]:
            song = content 
            artist = target if target and target!=content  else ""
            if modifier:
                return f"You want me to play '{song}' on Spotify by  {artist}. Shall I?"
            return f"You want me to play '{song}' on Spotify by {artist}. Shall I?"
        elif intent == "open_app":
            app = platform

            if app.lower().strip() =="whatsapp" :
                return f"You want me to open {app} and message {target} , {content}"
            return f"You want me to open {app}. Is that right?"
        
        elif intent == "search":
            query    = content or target or "something"
            platform_name = platform if platform not in ("unknown", "general") else "Google"
            return f"You want me to search for '{query}' on {platform_name}. Confirm?"
        else:
            action = intent.replace("_", " ")
            detail = target or content or ""
            if detail:
                return f"You want me to {action} — {detail}. Is that right?"
            return f"You want me to {action}. Is that right?"


    import urllib.parse

    def _handle_youtube(self, params: dict): 
        query = params.get("target", "") or params.get("content", "")
        query = query.strip()

        if not query:
            print("  [YouTube] No video name specified.")
            return {"status": "error", "message": "No query provided"}

        print(f"  [YouTube] Generating search URL for '{query}'...")
        
        # URL encode the query (e.g., "Iron Man" -> "Iron+Man")
        encoded_query = urllib.parse.quote(query)
        
      
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
      
        return {
            "status": "success", 
            "action": "open_url", 
            "url": url,
            "message": f"Opening YouTube for {query}"
        }

    def _handle_calender(self,params:dict) : 

        title = params.get('target') or params.get('content') or "Voice Assistant Meeting"
        date_str = params.get('date')
        time_str = params.get('time',"")

        if not date_str :
            print("Cannot schedule meeting. Missing date or time.")
            return
        
        print(f"Calling Calendar Api for {title} on {date_str} at {time_str}")

        result = create_event(title=title,date=date_str,time_str=time_str)

        if result["success"]:
            print(f"SUCCESS: {result['message']}")
            print(f"Link: {result['link']}")
        else:
            print(f"FAILED: {result['message']}")


    def _handle_spotify(self, params: dict):
        target    = params.get("target", "")
        content   = params.get("content", "")
        track_uri = params.get("track_uri")    # pre-resolved — skip search

        print(f"[Router] Spotify: '{content}' by '{target}'")
        result = play_on_spotify(target, content, track_uri=track_uri)

        if result["success"]:
            print(f"SUCCESS: {result['message']}")
        else:
            print(f"FAILED: {result['message']}")
        return result


    def _handle_whatsapp(self, params: dict):
        from integrations.whatsapp_handler import send_whatsapp_message

        matched_name   = params.get("target", "").strip()
        message        = params.get("content", "").strip()
        resolved_phone = params.get("resolved_phone", "").strip()

        if not message:
            print("  [WhatsApp] No message specified.")
            return {"success": False, "message": "No message to send."}

        if not resolved_phone:
            
            from integrations.whatsapp_handler import resolve_contact
            result = resolve_contact(matched_name)
            if not result["found"]:
                speaker_msg = result["message"]
                print(f"  [WhatsApp] {speaker_msg}")
                return {"success": False, "message": speaker_msg}
            resolved_phone = result["phone"]
            matched_name   = result["matched_name"]

        print(f"  [WhatsApp] Sending '{message}' to {matched_name} ({resolved_phone})")
        return send_whatsapp_message(
            phone        = resolved_phone,
            message      = message,
            matched_name = matched_name
        )

    def execute(self, intent_data : dict)  :
        if not intent_data : 
            return f"no intent data found"
        
        intent = intent_data.get("intent")
        platform = intent_data.get("platform")
        params = intent_data.get("parameters", {})

        print(f"Router Routing command: {intent} -> {platform}")
        if intent == "schedule_meeting" or platform == "calendar":
            result = self._handle_calender(params)
            return result or {"message": "Event created."}

        elif intent in ["play music", "play track", "play_media"] :
            result = self._handle_spotify(params)
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
            result = self._handle_whatsapp(params)
            return result or {"message": "Message sent."}

        elif platform == "youtube" or (intent in ["play music", "play track", "play_media","play_video"] and "youtube" in params.get("content", "").lower()):
            return self._handle_youtube(params)
        
