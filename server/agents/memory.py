from server.agent import AgentBase, AgentConfig
from shared.mixins import ResponseMixin
from shared.chaintools import text
from config.prompts import DETERMINE_SIMILAR_KEY, DETERMINE_IF_MEMORY
from server.llm import heal
from langchain_core.messages import AIMessage
import ast


class Memory(AgentBase):
    """The Memory Agent responsible for most memory storage."""

    def __init__(self, config: AgentConfig):
        self.redis = config.redis
        self.llm_ctx = config.llm_ctx

    def _store_memory_key_to_memories(self, key: str):
        """
        Store all stored memories to a memory list

        Args:
            key: the key to store"""
        keys = self.redis.lrange("agent_memory", 0, -1)
        if key not in keys:
            self.redis.lpush("agent_memory", key)

    async def store(self, key: str, memory: str | list, value_type: str = "str"):
        """
        Store a memory of type string or list

        Args:
            key: the key of the memory to store
            memory: the memory to store
            value_type: the value of the memory type. supports [str, list]
        """
        memory = str(memory)

        # Done with casting/conversions
        key = await self.ensure_key(key)
        # ensure key
        if value_type == "str":
            self.redis.set(f"memory|{key.lower()}", memory)
        elif value_type == "list":
            data = self.redis.lrange(name=key, start=0, end=-1)
            for item in memory:
                if item.lower() not in [
                    d.lower() for d in data
                ]:  # prevent duplicate, in future use a likeness function
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
        Ensure that the key exists, if not, use LLM to help determine

        Args:
            potential_key: the potential str of the key
        """
        key = self._to_memory_key(potential_key)
        if self.redis.exists(key):
            return key
        else:
            return self._to_memory_key(await self._determine_key_via_llm(potential_key))

    async def _determine_key_via_llm(self, non_key: str) -> str:
        """
        Determine the key via an LLM if its incorrect

        Args:
            non_key: the non correct key for the memory

        Returns:
            either a [str, ResponseMixin] depending if it needs the
            requesting chain to revalidate
        """

        like_keys: list[str] = self.redis.keys("memory|*")
        # remove the memory suffix
        like_keys = [key.replace("memory|", "") for key in like_keys]
        chain = DETERMINE_SIMILAR_KEY | self.llm_ctx.intent_llm | text
        res = await chain.ainvoke({"non_key": non_key, "list_of_keys": like_keys})
        if res.lower() == "none":
            # could not find key, creating new one
            return non_key
        else:
            return res

    async def retrieve(self, key: str, qty: int = -1):
        """
        Retrieve a stored memory

        Args:
            key: the memory key
            qty: optional, how many memories to get. default is all
        """
        key = self.ensure_key(key)
        data_type = self.redis.type(key)
        if data_type == "string":
            data = self.redis.get(key)
        elif data_type == "list":
            data = self.redis.lrange(key, 0, qty)
        return ResponseMixin(response=data, completed=True)

    def _to_memory_key(self, key: str):
        """
        Converts potential key to memory stored key

        Args:
            key: the potential key
        """
        return f"memory|{key}"

    def query(self):
        """
        Queries all data about Agent for the LLM"""

    async def understand_agent(self) -> ResponseMixin:
        """
        Method that returns a LLM understandable version of what this agent does
        """
        funcs = self._capture_functions()
        class_doc = Memory.__doc__
        return ResponseMixin(response=f"{class_doc} | Methods: {funcs}")

    async def _parse_memory_response(self, input: str):
        """ """
        input = text(input)
        if input.lower() == "none":
            return ResponseMixin(response="Nothing to remember", completed=True)

        commands = input.split(";")
        if len(input.split("|")) > 2 and len(commands) == 0:
            # issue with the AI response
            return ResponseMixin(
                response="You incorrectly responded. Please fix your response and only respond with the correct output.",
                retry=True,
                meta=text,
            )

        for cmd in commands:
            split = cmd.split("|")
            key = split[0]
            mod = split[1]
            if mod == "clear":
                self.forget(key)
            else:
                memory = split[2]
                await self.store(key=key, memory=memory, value_type=mod)
        return ResponseMixin(response="", completed=True)

    # async def llm_store(input: AIMessage) -> ResponseMixin:
    #     """
    #     Method for storing """

    async def _is_this_memorable(self, input: str) -> ResponseMixin:
        """ """
        llm = self.llm_ctx.reasoning_llm
        llm.invoke()
        chain = DETERMINE_IF_MEMORY | heal(llm.with_config(config={"llm_temperature": 0}), self._parse_memory_response)
        await chain.ainvoke({"text": input})
