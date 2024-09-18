from server.agent import AgentBase, AgentConfig
from shared.mixins import ResponseMixin

import ast

class Memory(AgentBase):
    def __init__(self, config: AgentConfig):
        self.redis = config.redis
        self.llm_ctx = config.llm_ctx

    def _store_memory_key_to_memories(self, key: str):
        keys = self.redis.lrange("agent_memory", 0, -1)
        if key not in keys:
            self.redis.lpush("agent_memory", key)

    def store(self, key: str, memory: str | list, value_type: str = "str"):
        """
        Store a memory of type string or list

        Args:
            mem
        """
        if value_type == "str" and not isinstance(memory, str):
            memory = str(memory)
        elif value_type == "list" and not isinstance(memory, list):
            try:
                ast.literal_eval(memory)
            except (ValueError, SyntaxError) as ex:
                return ResponseMixin(response="Could not convert memory to the type specified. Please try again.", retry=True, meta=ex)

        # Done with casting/conversions
        key = f"memory|{key.lower()}"
        if value_type == "str":
            self.redis.set(f"memory|{key.lower()}", memory)
        elif value_type == "list":
            data = self.redis.lrange(name=key)
            for item in data:
                if data.lower() not in data.lower(): # prevent duplicate, in future use a likeness function
                    self.redis.lpush(key, item)
        self._store_memory_key_to_memories(key)
        
    def forget(self, key: str):
        """
        Forget a memory

        Args:
            key: the memory key
        """
        res = self.redis.delete(key)
        return ResponseMixin(response=bool(res), completed=True)

    async def ensure_key(self, potential_key: str) -> str:
        """
        """
        ...
        
    async def _determine_key_via_llm(self, non_key: str):
        """
        """
        ...
        # determine key via LLM if needed
    async def get(self, key: str, qty: int = -1):
        """
        Get a stored memory

        Args:
            key: the memory key
            qty: optional, how many memories to get. default is all
        """
        data_type = self.redis.type(key)
        if data_type == "string":
            data = self.redis.get(key)
        elif data_type == "list":
            data = self.redis.lrange(key, 0, qty)
        return ResponseMixin(response=data, completed=True)

