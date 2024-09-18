from .models import LLMSettings
from .settings import Settings
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.language_models import BaseLanguageModel


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
