from openai.resources.audio import Speech
from .settings import Settings

from .models import VoiceSettings


class Voice:
    def __init__(self, settings: Settings, key: str | None):
        self.key = key
        self.settings: Settings
        self.cache_vs: VoiceSettings = self.__get_voice_settings()

    def __get_voice_settings(self) -> VoiceSettings:
        """Return the VoiceSettings model"""
        return self.settings.get("voice")

    def set_voice_agent(self, agent: str):
        self.cache_vs = self.settings.g

    def determine_voice_agent(self):
        vs = self.__get_voice_settings()
        if self.cache_vs.voice_agent != vs.voice_agent:
            ...

    def speak(self, input: str): ...
