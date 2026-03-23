import json
import pywhatkit
from datetime import datetime
import re 
from calendar_tools import create_event
from spotify_handler import play_on_spotify
from speech_to_text import NLUParser ,SpeechToText
from whatsapp_handler import load_google_contacts
import webbrowser
import time
import urllib.parse
import pyautogui
import pyperclip

class ActionRouter : 


    def __init__(self) :
        self.contacts = load_google_contacts()

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
            artist = target if target else ""
            if modifier:
                return f"You want me to play '{song}' on Spotify by  {artist}. Shall I?"
            return f"You want me to play '{song}' on Spotify by {artist}. Shall I?"
        
        elif intent == "open_app":
            app = target or content or "an app"
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
        

    def _find_contact(self,name:str) ->str |None : 
        name_to_check = name.lower()
        if name_to_check in self.contacts:
            return self.contacts[name_to_check]
        print(f"ALL CONTACTS {self.contacts}")
        
        for saved_name, number in self.contacts.items():
            if name_to_check in saved_name or saved_name in name_to_check:
                print(f"  [Contacts] Matched '{name}' → '{saved_name}'")
                return number
        return None

    def _handle_calender(self,params:dict) : 

        title = params.get('target') or params.get('content') or "Voice Assistant Meeting"
        date_str = params.get('date')
        time_str = params.get('time')

        if not date_str or not time_str:
            print("Cannot schedule meeting. Missing date or time.")
            return
        
        print(f"Calling Calendar Api for {title} on {date_str} at {time_str}")

        result = create_event(title=title,date=date_str,time_str=time_str)

        if result["success"]:
            print(f"SUCCESS: {result['message']}")
            print(f"Link: {result['link']}")
        else:
            print(f"FAILED: {result['message']}")


    def _handle_spotify(self,params:dict) : 
        target = params.get("target", "")   
        content = params.get("content", "") 
        query_parts = [p for p in [content, target] if p]
        query = " ".join(query_parts)
        
        if not query:
            print("[Router Error]: Nothing to play.")
            return
            
        print(f"[Router] Calling Spotify API for: {query}")
        result = play_on_spotify(query)
        
        if result["success"]:
            print(f"SUCCESS: {result['message']}")
        else:
            print(f"FAILED: {result['message']}")


    def _handle_whatsapp(self,params : dict) : 
        contact =  params.get("target","").strip()
        message = params.get("content","").strip()

        if not contact:
            print("  [WhatsApp] No contact specified.")
            return

        if not message:
            print("  [WhatsApp] No message specified.")
            return
        
        phone = self._find_contact(contact)

        if not phone:
            print(f"  [WhatsApp] '{contact}' not found in contacts.")
            return
        
        phone_clean = phone.replace("+", "").replace(" ", "")
        encoded_msg = urllib.parse.quote(message)

        # WhatsApp Web direct message URL — opens chat directly
        url = f"https://web.whatsapp.com/send?phone={phone_clean}&text={encoded_msg}"

        print(f"  [WhatsApp] Opening chat with {contact}...")

        # open in existing browser window — won't duplicate if already open
        webbrowser.open(url)

        # wait for WhatsApp Web to load the chat
        time.sleep(8)

        # press Enter to send — message is already filled in the URL
        pyautogui.press("enter")

        print(f"  ✅ Message sent to {contact}")

    def execute(self, intent_data : dict)  :
        if not intent_data : 
            return f"no intent data found"
        
        intent = intent_data.get("intent")
        platform = intent_data.get("platform")
        params = intent_data.get("parameters", {})

        print(f"Router Routing command: {intent} -> {platform}")
        if intent == "schedule_meeting" or platform == "calendar":
            self._handle_calender(params)

        elif intent in ["play music","play track","play_media"] or platform =="spotify" :
               if platform =="unknown" :
                   platform = "spotify"
               self._handle_spotify(params)
        elif intent == "send_message" and platform == "whatsapp":  
             if platform =="general" :
                   platform = "whatsapp"
             self._handle_whatsapp(params)
        



if __name__ == "__main__": 
    
    stt = SpeechToText()
    nlu = NLUParser()

    router = ActionRouter()

    raw_text = stt.listen()
    
    if raw_text:
        print(f"\n[Raw Transcript]: {raw_text}")
        print("[NLU] Extracting intent...")
        
        parsed_data = nlu.parse(raw_text)
        
        print("\n[Final JSON Payload]:")
        print(json.dumps(parsed_data, indent=4))
        
        question =router.generate_confirmation_prompt(parsed_data)
        print(f"[System] {question}")
        
        print("   (Listening for confirmation...)")
        
        stt.recognizer.pause_threshold = 0.5 
        confirmation_text = stt.listen()
        stt.recognizer.pause_threshold = 0.8 
        if confirmation_text:
            cleaned_reply = confirmation_text.lower()
            print(f"   [You]: {cleaned_reply}")
            positive_words = ["yes", "yeah", "yep", "sure", "do it", "ok", "okay", "please"]
            
            if any(word in cleaned_reply for word in positive_words):
                print("\n[System]: Confirmation received. Executing action...")
                router.execute(parsed_data)
            else:
                print("\n[System]: Action cancelled by user.")
        else:
            print("\n[System]: No confirmation heard. Action cancelled.")
    
        
    else:
        print("\n[Pipeline Cancelled]: No audio input.")
    
