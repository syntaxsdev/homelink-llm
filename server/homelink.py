from .intents import IntentEngine, IntentResponse
from .settings import Settings, SettingsResponse
from .voice import Voice
from .llm import LLMContext
from .agent import AgentBase, AgentConfig

from shared.mixins import ResponseMixin

from .agents import Memory, Conversations
from shared.utils import load_yaml, Colors
from config.prompts import CASUAL_CHAT

from redis import Redis

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
        self.settings = Settings(
            settings=stgs, settings_opt=stgs_opt, client=client, redis=self.redis
        )
        self.llm_context = LLMContext(settings=self.settings)

        self.voice = Voice(settings=self.settings)

        # Create AgentConfig
        self.agent_config = AgentConfig(
            redis=self.redis, llm_ctx=self.llm_context, settings=self.settings
        )

        # Load Main Agents
        self.memory = Memory(config=self.agent_config)
        self.conversations = Conversations(config=self.agent_config)

        # maybe if it makes sense in the future, abstract memory to be a core comp.
        # so it can be added to the config?
        self.conversations._inject_memory_agent(self.memory)

        intent_data = load_yaml(intents_file)
        self.intents_engine = IntentEngine(
            intents=intent_data, llm=self.llm_context.intent_llm
        )

    async def send_chat(self, input: str):
        """
        Sends a chat to the current conversational context

        Args:
            input: the initial chat message
        """
        memorable: ResponseMixin = await self.memory._is_this_memorable(input)
        print(
            f"{Colors.YELLOW}Input:{Colors.RESET}{Colors.GREEN}",
            memorable.response,
            Colors.RESET,
        )

        response: str = await self.conversations.conversate(input)

        return ResponseMixin(response=response, completed=True)

    async def execute_link(self, input: str):
        """
        Execute a link
        """
        response: IntentResponse = await self.determine_intent(input)  # TODO:FIX
        if response.intent:
            intent_execution = await self.execute_intent(response)
        else:
            response: ResponseMixin = await self.memory._is_this_memorable(input)
            if not response or not response.completed:
                # build a res
                print("Issue with memory saving")
            response = await self.conversations.conversate(input)

            # response = await chain.ainvoke({'text': input})
            # audio_file = await self.voice.tts(response.content)
            # return audio_file

    async def determine_intent(self, input: str) -> IntentResponse:
        """
        Gets intents from Intent Engine

        Args:
            input: the requested input string
        """
        return await self.intents_engine.determine_intent(input)

    async def execute_intent(self, intent: IntentResponse):
        """Execute the intent

        Args:
            intent: The IntentResponse to execute
        """
