from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os 

def load_google_contacts()-> dict:
    try : 
        scopes = ["https://www.googleapis.com/auth/contacts.readonly"]

        creds = None 
        if os.path.exists('context_token.json') : 
            creds = Credentials.from_authorized_user_file("context_token.json",scopes)
        
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json",scopes)
            creds = flow.run_local_server(port=0)

            with open("context_token.json","w") as f :
                f.write(creds.to_json())

        service = build("people","v1",credentials=creds)

        results = service.people().connections().list(
            resourceName   = "people/me",
            pageSize       = 1000,
            personFields   = "names,phoneNumbers"
        ).execute()

        contacts = {}
        for person in results.get("connections", []):
            names   = person.get("names", [])
            phones  = person.get("phoneNumbers", [])
            if names and phones:
                name   = names[0].get("displayName", "").lower()
                number = phones[0].get("value", "").replace(" ", "").replace("-", "")
                if not number.startswith("+"):
                    number = f"+91{number[-10:]}"
                contacts[name] = number

        print(f"  [Contacts] Loaded {len(contacts)} from Google Contacts")
        return contacts

    except Exception as e:
        print(f"  [Contacts] Google Contacts error: {e}")
        return {}
    
