from redis import Redis
from .llm import LLMContext

from shared.mixins import ResponseMixin
from dataclasses import dataclass


@dataclass
class AgentConfig:
    redis: Redis
    llm_ctx: LLMContext



class AgentBase:
    """
    The base Agent class for all other extendable agents

    Args:
        llm_ctx: the LLM context
        redis: the Redis object
    """

    def __init__(self, config: AgentConfig):
        self.config = config

    def query(self):
        ...

    
