from pydantic import BaseModel


class CalendarCredentialsPayload(BaseModel):
    # The full contents of the user's own credentials.json (Desktop-app OAuth client)
    credentials_json: str
