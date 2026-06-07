from pydantic import BaseModel


class AppPayload(BaseModel):
    name: str
    path: str = ""


class BrowserPayload(BaseModel):
    name: str
