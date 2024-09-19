from .intents import IntentEngine, IntentResponse
from .settings import Settings, SettingsResponse
from .voice import Voice
from .llm import LLMContext
from .agent import AgentBase, AgentConfig

from shared.mixins import ResponseMixin

from .agents import Memory
from shared.utils import load_yaml
from config.prompts import CASUAL_CHAT

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
        intents_file = f"{config_folder}/intents.yml"
        client = f"{config_folder}/client.yml"

        if not os.path.exists(stgs):
            raise FileNotFoundError(
                f"Could not find settings.yml in config folder {config_folder}."
            )

        if not os.path.exists(stgs_opt):
            raise FileNotFoundError(
                f"Could not find SETTINGS_OPT.yml in config folder {config_folder}."
            )

        if not os.path.exists(intents_file):
            raise FileNotFoundError(
                f"Could not find intents.yml in config folder {config_folder}."
            )
        
        # if not os.path.exists(client):
        #     raise FileNotFoundError(
        #         f"Could not find client.yml in config folder {config_folder}."
        #     )

        port: str = os.getenv("REDIS_PORT") or 6379
        host: str = os.getenv("REDIS_HOST") or "localhost"

        # Create the Redis object
        self.redis = Redis(host=host, port=port, decode_responses=True)

        # Set the settings
        self.settings = Settings(settings=stgs, settings_opt=stgs_opt, client=client, redis=self.redis)
        self.llm_context = LLMContext(settings=self.settings)

        self.voice = Voice(settings=self.settings)

        # Create AgentConfig
        self.agent_config = AgentConfig(redis=self.redis, llm_ctx=self.llm_context)

        # Load Main Agents
        self.memory = Memory(config=self.agent_config)

        intent_data = load_yaml(intents_file)
        self.intents_engine = IntentEngine(
            intents=intent_data, llm=self.llm_context.intent_llm
        )

    async def execute_link(self, input: str):
        """
        Execute a link
        """
        response: IntentResponse = await self._get_intent(input) # TODO:FIX
        if not response.intent:
            response: ResponseMixin = await self.memory._is_this_memorable(input)
            if not response or not response.completed:
                # build a res
                print("Issue with memory saving")
            chain = CASUAL_CHAT | self.llm_context.reasoning_llm
            response = await chain.ainvoke({'text': input})
            audio_file = await self.voice.tts(response.content)
            return audio_file
            


    async def _get_intent(self, input: str) -> IntentResponse:
        """
        Gets intents from Intent Engine
        """
        return await self.intents_engine.determine_intent(input)
