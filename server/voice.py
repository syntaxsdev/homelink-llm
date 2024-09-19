from openai import AsyncClient
from openai.resources.audio import AsyncSpeech
from .settings import Settings

from tempfile import TemporaryFile

from .models import VoiceSettings

import io

class Voice:
    def __init__(self, settings: Settings):
        try:
            self.openai_client = AsyncClient()
        except Exception:
            raise EnvironmentError(
                "Could not authenticate to OpenAI for voice services"
            )

        self.settings = settings
        self.voice_settings = settings.voice

        self.speech_system = self.construct_speech_system()

    def refresh_speech_system(self):
        self.tts = self.construct_speech_system()

    def construct_speech_system(self):
        """
        Construct the speech system
        """
        voice = self.voice_settings
        if voice.voice_lib == "openai":
            return AsyncSpeech(client=self.openai_client)
        elif voice.voice_lib == "local":
            raise NotImplementedError("local voice library is not implemented")

    def __get_voice_settings(self) -> VoiceSettings:
        """Return the VoiceSettings model"""
        return self.settings.get("voice")

    def set_voice_agent(self, agent: str):
        self.cache_vs = self.settings.g

    def determine_voice_agent(self):
        vs = self.__get_voice_settings()
        if self.cache_vs.voice_agent != vs.voice_agent:
            ...

    async def tts(self, input: str, *args):
        """
        Use speech system to execute text to speech

        Args:
            input: the string to turn to speech
        """
        vs = self.voice_settings
        if vs.voice_lib == "openai":
            data = await AsyncSpeech(client=self.openai_client).create(
                input=input,
                model=vs.voice_model,
                voice=vs.voice_agent,
                response_format="mp3",
                speed=vs.voice_pitch,
            )
            temp_bytes = io.BytesIO()
            temp_bytes.write(data.content)
            temp_bytes.seek(0)
            return temp_bytes
            # with TemporaryFile(mode="w+b", suffix=".mp3") as tmpfile:
            #     tmpfile.write(data.content)
            #     print("file name", tmpfile.name)
            #     return tmpfile.name