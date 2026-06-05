from pydantic import BaseModel


class SignupPayload(BaseModel):
    display_name: str
    email: str
    password: str


class LoginPayload(BaseModel):
    email: str
    password: str
