from redis import Redis
from .llm import LLMContext

from shared.mixins import ResponseMixin
from dataclasses import dataclass
from .settings import Settings

@dataclass
class AgentConfig:
    redis: Redis
    llm_ctx: LLMContext
    settings: Settings


class AgentBase:
    """
    The base Agent class for all other extendable agents

    Args:
        llm_ctx: the LLM context
        redis: the Redis object
    """

    def __init__(self, config: AgentConfig):
        self.config = config

    def query(self): ...

    @classmethod
    def _capture_functions(cls) -> dict:
        return {
            func: getattr(cls, func).__doc__
            for func in dir(cls)
            if callable(getattr(cls, func)) and not func.startswith("_")
        }
