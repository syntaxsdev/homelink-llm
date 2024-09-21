from shared.mixins import ResponseMixin
from config.prompts import INTENT_TIE_BREAK
from .models import Intent
from langchain_core.language_models import BaseLanguageModel

from dataclasses import dataclass


@dataclass
class IntentResponse(ResponseMixin):
    intent: Intent = None
    query: bool = False


class IntentEngine:
    """
    Efficient system for determining intent and using LLM as tie break

    Args:
        llm: the LLM model from Langchain
    """

    def __init__(self, intents: dict, llm: BaseLanguageModel):
        self.llm = llm

        try:
            self.intents = [Intent.model_validate(item) for item in intents["intents"]]
        except Exception:
            raise AttributeError(
                "Please check your intents.yml file for attribute issues"
            )

    def empty_intent(self, response: any) -> callable:
        """Empty intent

        Args:
            response: AIMessage or any returned response. Will just forward as output
        """
        return response

    async def determine_intent(self, input: str) -> IntentResponse:
        """
        Determine intent based off keywords
        If not fallback to LLM for tie break on multiple options or no options
        This saves cost as only some calls will be used as the intent agent

        Args:
            input: the user query string
        """

        intent_count = await self._count_intent(input)
        max_count = max(intent_count.values())
        if max_count == 0:  # no intents found
            return IntentResponse(response="No intent")  # todo

        top_intents, max_count, has_multiple = await self._get_top_intent(intent_count)
        # add back typing
        top_intents: dict[str, int] = top_intents

        if not has_multiple:
            return IntentResponse(
                response="", intent=self._get_intent_data(top_intents[0]), query=False
            )

        if has_multiple and (len(top_intents) > 1):
            intents_for_tiebreak = {}
            for key in top_intents:
                max_for_intent = intent_count[key]
                intent = self._get_intent_data(key)
                intents_for_tiebreak[key] = {
                    "description": intent.description,
                    "keywords": intent.keywords,
                    "likely_correct_intent_score": max_for_intent,
                    "query": intent.query.when if intent.query else [],
                }
            chosen = await self.llm_tiebreak(
                input=input, top_intents=intents_for_tiebreak
            )
            return chosen

    async def llm_tiebreak(
        self, input: str, top_intents: dict[str, int], tries: int = 1
    ) -> IntentResponse:
        """
        Breaks tie for similar intent

        Args:
            input: the input string
            top_intents: dictionary of the top intents
        """
        if tries == 3:
            return None
        chain = INTENT_TIE_BREAK | self.llm
        msg_ctx = await chain.ainvoke({"input": input, "intent_data": str(top_intents)})
        response: str = msg_ctx.content
        if response.lower() == "none":
            return IntentResponse(response="No intent")
        # query tag
        query = response.find("?") > 0

        intent: Intent = self._get_intent_data(response.strip().replace("?", ""))

        if not intent:
            tries += 1
            return await self.llm_tiebreak(input, top_intents, tries)
        return IntentResponse(response="", intent=intent, query=query)

    async def _count_intent(self, input: str) -> dict[str, int]:
        """
        Count the intents into a dict
        """
        input = input.lower()
        intent_count: dict = {}
        for intent in self.intents:
            intent_count[intent.name] = 0
            for word in intent.keywords:
                word = word.lower()
                if word in input:
                    intent_count[intent.name] += 1
        return intent_count

    async def _get_top_intent(self, intents: dict[str, int]) -> list[str]:
        """
        Get the top intents
        """
        top_intents = []
        max_count = None

        for intent, count in intents.items():
            if (max_count is None) or (count > max_count):
                max_count = count
                top_intents = [intent]
            elif count == max_count:
                top_intents.append(intent)

        has_multiple = len(top_intents) > 1
        return top_intents, max_count, has_multiple

    def _get_intent_data(self, key: str) -> Intent:
        """
        Get intent for key/name

        Args:
            key: the intent key
        """
        if not self.intents:
            return None
        intent = [intent for intent in self.intents if intent.name == key]
        if len(intent) > 0:
            return intent[0]
