from .intents import IntentEngine, IntentResponse
from .settings import Settings, SettingsResponse
from .voice import Voice
from .llm import LLMContext

from redis import Redis

import asyncio
import os


class HomeLink:
    """The connecting system for the HomeLink system

    Args:
        config_folder: the configuration folder
    """

    def __init__(self, config_folder: str):
        stgs = f"{config_folder}/settings.yml"
        stgs_opt = f"{config_folder}/SETTINGS_OPT.yml"

        if not os.path.exists(stgs):
            raise FileNotFoundError(
                f"Could not find settings.yml in config folder {config_folder}."
            )

        if not os.path.exists(stgs_opt):
            raise FileNotFoundError(
                f"Could not find SETTINGS_OPT.yml in config folder {config_folder}."
            )

        port: str = os.getenv("REDIS_PORT") or 6379
        host: str = os.getenv("REDIS_HOST") or "localhost"

        # Create the Redis object
        self.redis = Redis(host=host, port=port)

        # Set the settings
        self.settings = Settings(settings=stgs, settings_opt=stgs_opt, redis=self.redis)
        self.llm_context = LLMContext(settings=self.settings)
        
        self.voice = Voice(settings=self.settings)

        self.intents_engine = IntentEngine(llm=self.llm_context.intent_llm)
        

    async def execute_link(self, input: str):
        """
        Execute a link     
        """

        ...
        