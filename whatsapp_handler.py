from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os 
from thefuzz import fuzz 

class WhatsappHandler() : 

    def __init__(self) : 
        self.contacts = {} 
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

        
            for person in results.get("connections", []):
                names   = person.get("names", [])
                phones  = person.get("phoneNumbers", [])
                if names and phones:
                    name   = names[0].get("displayName", "").lower()
                    number = phones[0].get("value", "").replace(" ", "").replace("-", "")
                    if not number.startswith("+"):
                        number = f"+91{number[-10:]}"
                    self.contacts[name] = number

            print(f"  [Contacts] Loaded {len(self.contacts)} from Google Contacts")

        except Exception as e:
            print(f"  [Contacts] Google Contacts error: {e}")
    
    def find_contact(self,name:str) ->str |None : 
            
            if not self.contacts:
                print("  [Contacts] No contacts available in memory.")
                return None
        
            name_to_check = name.lower()

            best_score = -999
            best_contact = None

            for contact in self.contacts : 
                single_contact = contact.lower()
                base_score= fuzz.token_set_ratio(name_to_check,single_contact)

                exact_bonus = 0

                if name_to_check == contact : 
                    exact_bonus = 20 
                elif name_to_check in contact.split() : 
                    exact_bonus = 5

                length_penalty = 0
                if exact_bonus == 0:
                    diff = abs(len(contact) - len(name_to_check))
                    length_penalty = diff * 0.5 

                # Combine scores
                final_score = base_score + exact_bonus - length_penalty

                if final_score > best_score : 
                    best_score = final_score 
                    best_contact = contact 

            # if name_to_check in self.contacts:
            #     return self.contacts[name_to_check]
            # print(f"ALL CONTACTS {self.contacts}")
            
            # for saved_name, number in self.contacts.items():
            #     if name_to_check in saved_name or saved_name in name_to_check:
            #         print(f"  [Contacts] Matched '{name}' → '{saved_name}'")
            number = self.contacts[best_contact]
            return number
        