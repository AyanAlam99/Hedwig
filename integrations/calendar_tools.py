import os 
import json 
from datetime import datetime , timedelta 
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import wave

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_FILE = "token.json"
CREDS_FILE = "credentials.json"
TIMEZONE   = "Asia/Kolkata"


def _get_service() : 

    if not os.path.exists(CREDS_FILE) : 
        raise FileNotFoundError(
            f"credentials.json not found"
        )
    
    creds = None 

    if os.path.exists(TOKEN_FILE) :
        creds  = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print(" Calendar - Refreshing token...")
                creds.refresh(Request())
            except Exception as e:
                print(f"  Calendar - Refresh failed: {e}. Re-authenticating...")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE) # Force removal of the bad token
                
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            print(f"Opening Browser for google calendar auth (First time or manual login)")
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
            print(" Authorized. token.json saved.\n")
 
    return build("calendar", "v3", credentials=creds)



def create_event(
        title : str , 
        date : str , 
        time_str : str  = "15:00",
        duration_minutes : int = 60,
        description : str ="",
        attendees : list[str] = None
        ) -> dict : 
    if not title : 
        return {"success":False, "message":"Event title is required"}
    if not date: 
        return {"success":False , "message":"Date is required"}
    
    if not time_str:   
        time_str = "15:00"
    
    try : 
        start_dt = datetime.strptime(f"{date} {time_str}" ,"%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes = duration_minutes)

    except ValueError : 
        return {
            "success" : False ,
            "message" : f"Invalid date/time format: {date} {time_str}. Expected YYYY-MM-DD and HH:MM."
        } 
    
    event_body = {
        "summary" : title,
        "description" : description , 
        "start" : {
            "dateTime": start_dt.isoformat(),
            "timeZone": TIMEZONE,
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": TIMEZONE,
        },

        "reminders" : {
            "useDefault" : False ,
            "overrides" : [
                {"method": "popup",  "minutes": 10},
                {"method": "email",  "minutes": 30},
            ],
        },
    }

    if attendees : 
        event_body["attendees"] = [{"email":e} for e in attendees]
    
    try : 
        service = _get_service()
        event = service.events().insert(
            calendarId = "primary",
            body = event_body , 
            sendUpdates = "all" if attendees else "none"
        ).execute()

        spoken_time = start_dt.strftime("%B %d at %I:%M %p").lstrip("0")
 
        return {
            "success":  True,
            "event_id": event.get("id"),
            "link":     event.get("htmlLink"),
            "message":  f"{title} created for {spoken_time}."
        }
 
    except Exception as e:
        error = str(e)
        print(f"  Calendar API error: {error}")
        return {
            "success": False,
            "message": f"Couldn't create the event. Error: {error}"
        }

    




