from pydantic import BaseModel


class IntentQuery(BaseModel):
    when: list[str]

class Intent(BaseModel):
    name: str
    agent: str
    description: str
    keywords: list[str] | None
    query: IntentQuery | None = None


# Settings

class VoiceSettings(BaseModel):
    voice_lib: str
    voice_agent: str
    voice_model: str
    voice_pitch: float


class LLMSettings(BaseModel):
    reasoning_llm: str
    reasoning_llm_model: str
    intent_llm: str
    intent_llm_model: str

class SettingsModel(BaseModel):
    voice_agent: str
