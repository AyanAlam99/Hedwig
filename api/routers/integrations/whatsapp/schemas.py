from pydantic import BaseModel


class WhatsAppConnectPayload(BaseModel):
    instance_id: str
    api_token: str


class ContactPayload(BaseModel):
    name: str
    phone: str


class RemoveContactPayload(BaseModel):
    name: str
