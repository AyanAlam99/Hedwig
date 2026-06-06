from pydantic import BaseModel, field_validator, model_validator

_PLAY_ALIASES = {"play", "play music", "play track", "play_media"}
_PAUSE_MODIFIER = {"pause"}
_RESUME_MODIFIERS = {"resume", "continue", "unpause"}


class Parameters(BaseModel):
    target: str = ""
    content: str = ""
    action_modifier: str = ""
    date: str = ""
    time: str = ""

    @field_validator("target", "content", "action_modifier", "date", "time", mode="before")
    @classmethod
    def conv_str(cls, v):
        return str(v).strip() if v is not None else ""


class IntentData(BaseModel):
    intent: str = "unknown"
    platform: str = "unknown"
    parameters: Parameters = Parameters()

    @field_validator("intent", "platform", mode="before")
    @classmethod
    def conv_str(cls, v):
        return str(v).strip().lower() if v is not None else "unknown"

    @model_validator(mode="after")
    def normalize(self):
        
        if self.intent in _PLAY_ALIASES:
            self.intent = "play_media"

        modifier = self.parameters.action_modifier.lower()
        if modifier in _PAUSE_MODIFIER:
            self.intent = "pause"
            self.platform = "spotify"
        elif modifier in _RESUME_MODIFIERS:
            self.intent = "resume"
            self.platform = "spotify"

        return self
