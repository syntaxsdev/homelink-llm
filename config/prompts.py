from langchain_core.prompts import PromptTemplate

INTENT_TIE_BREAK = PromptTemplate.from_template(
    "Determine the action only if the user expresses a desire to execute something related to the context provided. | Input: {input}. | Intent data: {intent_data} | If none match, return 'None' and skip next step. | ONLY Return the `key`."
)
