from langchain_core.prompts import PromptTemplate

INTENT_TIE_BREAK = PromptTemplate.from_template(
    """
    Determine the action only if the user explicitly expresses a desire to execute something or if the query context provided aligns closely with the intent.
    | Input: {input}. 
    | Intent data: {intent_data}
    | If the match is based on the query of the intent, return: the `key` and `?`
    | If none match, return 'None' and skip next step. 
    | ONLY Return the `key`.
    """
)
