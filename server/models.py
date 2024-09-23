from pydantic import BaseModel, Field
from datetime import datetime
from langchain_core.chat_history import InMemoryChatMessageHistory


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


class ConversationMemory(InMemoryChatMessageHistory):
    """Higher order implementation of InMemoryChatMessageHistory
    to help with conversational awareness
    """

    start_datetime: datetime
    last_datetime: datetime | None = None
    end_reason: str | None = None
    ended_conversation: bool = False
    conversation_highlights: list[str] = Field(default_factory=list)
