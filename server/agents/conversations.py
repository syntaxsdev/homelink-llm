from server.agent import AgentBase, AgentConfig
from server.llm import heal, HealHelper
from server.models import ConversationMemory
from .memory import Memory
from config.prompts import CASUAL_CHAT, MEMORY_PICKER
from shared.mixins import ResponseMixin

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda
from uuid import uuid4


class Conversations(AgentBase):
    """
    Internal agent for conversations
    """

    def __init__(self, config: AgentConfig):
        # self.config = config
        self.reasoning_llm = config.llm_ctx.reasoning_llm
        self.task_llm = config.llm_ctx.reasoning_llm  # change to task
        self.settings = config.settings

        self.assistant_name = self.settings.get("assistant").response["name"]

    async def conversate(self, input: str) -> str:
        """Engage in seamless conversation without
        having to manage previous context

        Args:
            input: str
        """

        # Generate a convo id if not one (first run potentially)
        if not hasattr(self, "convo_id"):
            self.convo_id = self._generate_short_key()
        convo_id = self.convo_id

        convo_memory = self.memory.get_chat_session(convo_id)

        # Check if conversation was ended by system
        if convo_memory.ended_conversation:
            convo_id = self._generate_short_key()
            convo_memory = self.memory.get_chat_session(convo_id)

        prompt_objs = {"assistant_name": self.assistant_name}

        # This is not the standard, but for the love of me their documentation is so poorly written
        # It is impossible to understand what to do after hours of testing, so we will omit using
        # Any automatic history tracking from them. Its probably better this way :)

        # Allow healing
        chain = CASUAL_CHAT | heal(self.reasoning_llm, self.ensure_conversation)

        # Manual tracking

        chat_history = convo_memory.messages
        print("Input was", input)
        llm_res = await chain.ainvoke(
            {"chat_history": chat_history, "message": input, **prompt_objs}
        )
        ai_response = llm_res.response
        convo_memory.add_user_message(HumanMessage(input))
        convo_memory.add_ai_message(AIMessage(ai_response))
        print("convo entire mem", convo_memory.messages)
        return ai_response

    def get_convo_memory(self, session_id: str) -> ConversationMemory:
        convo = self.memory.get_chat_session(session_id)
        convo_len = len(convo.messages)
        if convo_len > 5:
            ...
        return convo

    async def memory_heal_helper(self, memory: ConversationMemory) -> AIMessage:
        """Allows healing to happen with conversation models
        This is an implementation of how a `heal_helper` could work

        Args:
            memory: The conversation memory to help aid in memory healing
        """
        keys_list = await self.memory.list_of_keys()

        async def heal_helper(heal_config: HealHelper):
            memory_data: dict[str, str] = {}
            llm_input: ChatPromptValue = heal_config.llm_input
            last_message: HumanMessage = llm_input.messages[-1].content
            print("lmc", last_message)
            chain = MEMORY_PICKER | self.task_llm
            response = await chain.ainvoke(
                {"user_response": last_message, "memories": keys_list}
            )
            mem: str = response.content
            print("Memory that AI chose:", mem)

            # Multiple memories requested
            keys = [mem]
            if mem.find(",") > 0:
                keys = mem.split(",")

            for key in keys:
                key_real = await self.memory.exists(key)
                if key_real:
                    response_data = await self.memory.retrieve(key)
                    memory_data[key] = response_data.response

            # if empty
            if not memory_data:
                memory_data = "User does not have any memories related. Request information from user, but keep it brief."
            final_message = f"{last_message} | Memory Bank: {str(memory_data)}"
            print(final_message)
            return final_message

        return heal_helper

    async def ensure_conversation(self, input):
        """
        Ensure AI reponse to conversation or heal
        """
        response: str = input.content
        print("RESPONSE", response)
        # A memory reuest was called
        if response.find("!memory_request!") >= 0:
            return ResponseMixin(
                response="Memory was requested",
                retry=True,
                helper=await self.memory_heal_helper(self.memory),
            )

        return ResponseMixin(response=response, completed=True)

    def _generate_short_key(self):
        """
        Generate a short key

        Returns:
            the short uuid
        """
        return str(uuid4())[:8]

    def _inject_memory_agent(self, memory: Memory):
        """
        Used to innject the memory storage

        Args:
            memory: the Memory agent
        """
        self.memory = memory
