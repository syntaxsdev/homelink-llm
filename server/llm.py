from .models import LLMSettings
from .settings import Settings
from shared.mixins import ResponseMixin
from config.prompts import HEAL_PROMPT_SECOND_ATTEMPT, HEAL_PROMPT_FIRST_ATTEMPT
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain.chains.base import Chain
from langchain.chains.sequential import SequentialChain
from langchain_core.runnables import RunnableLambda
from dataclasses import dataclass
from typing import Any, Callable
import inspect


class LLMContext:
    """
    Context Manager for LLMs

    Args:
        settings: The Settings object
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        llm_settings = settings.llm
        self.llm_settings = llm_settings

        # Reasoning LLM
        self._reasoning_llm = construct_llm(
            llm_settings.reasoning_llm, llm_settings.reasoning_llm_model
        )

        # Intent LLM
        self._intent_llm = construct_llm(
            llm_settings.reasoning_llm, llm_settings.reasoning_llm_model
        )

    @property
    def intent_llm(self) -> BaseLanguageModel:
        return self._intent_llm

    @property
    def reasoning_llm(self) -> BaseLanguageModel:
        return self._reasoning_llm

    @intent_llm.setter
    def intent_llm(self, value: BaseLanguageModel):
        self._intent_llm = value

    @reasoning_llm.setter
    def reasoning_llm(self, value: BaseLanguageModel):
        self._reasoning_llm = value


@dataclass
class HealHelper:
    llm_input: any
    llm_response: AIMessage
    action_response: ResponseMixin
    retry_count: int


def heal(
    llm: BaseLanguageModel,
    action: Callable[[Any], ResponseMixin],
    retry_max: int = 3,
):
    """
    Heals any functions from a bad LLM response. You must return a `ResponseMixin`
    indicating to retry and pass some metadata to `meta` if you want to give additional context

    Args:
        llm: The BaseLanguageModel (llama, openai, anthropic, ..etc)
        action: the Runnable function that takes in a parameter. Must return a ResponseMixin
        retry_max: default set to 3, how many times to retry

    Examples:
        ```py
        chain = prompt | heal(llm, action)
        await chain.ainvoke({})
        ```
    """

    async def healer(input, retry: int = 0):
        original_input = input

        async def invoke(local_input):
            llm_response = await llm.ainvoke(local_input)

            response: ResponseMixin = await action(llm_response)
            return llm_response, response

        while retry < retry_max:
            llm_response, response = await invoke(input)
            if not response.retry:
                return response

            # If provided a helper
            if response.helper:
                heal_config = HealHelper(
                    llm_input=original_input,
                    llm_response=llm_response,
                    action_response=response,
                    retry_count=retry,
                )
                if inspect.iscoroutinefunction(response.helper):
                    input = await response.helper(heal_config)
                else:
                    input = response.helper(heal_config)
            else:
                if retry == 0:
                    input = await HEAL_PROMPT_FIRST_ATTEMPT.ainvoke(
                        {
                            "request": input,
                            "meta": str(response.meta),
                            "mixin_response": response.response,
                        }
                    )

                elif retry >= 1:
                    input = await HEAL_PROMPT_SECOND_ATTEMPT.ainvoke(
                        {
                            "previous": original_input,
                            "previous_response": llm_response,
                            "meta": str(response.meta),
                        }
                    )
            retry += 1

        return response

    return RunnableLambda(healer)


def construct_llm(llm: str, llm_model: str) -> BaseLanguageModel:
    """
    Contruct LLM from params

    Args:
        llm: the LLM type
        llm_model: the LLM model
    """
    if llm == "openai":
        if "davinci" in llm_model or "babbage" in llm_model:
            return OpenAI(model=llm_model)
        else:
            return ChatOpenAI(model=llm_model)
    elif llm == "llama":
        raise NotImplementedError("LLama is not implemented yet")
