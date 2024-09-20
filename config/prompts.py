from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

HEAL_PROMPT_FIRST_ATTEMPT = PromptTemplate.from_template(
    """
    Please read the instructions carefully.
    {request}
    Helper metadata: {meta}
    """
)

HEAL_PROMPT_SECOND_ATTEMPT = PromptTemplate.from_template(
    """
    You incorrectly responded in your last request.
    Please fix your response and ONLY respond with the correct output described below.
    Previous Request: <{previous}>
    Your previous response which was incorrectly formatted: <{previous_response}>
    Additional information: {mixin_response}
    Helper metadata: {meta}
    """
)

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

DETERMINE_SIMILAR_KEY = PromptTemplate.from_template(
    """
    Determine the key from the list most similar to the key: `{non_key}`
    Keys can be matched based on context as well, such as "eggs_needed" -> "shopping_list"
    | List of real keys: `{list_of_keys}`
    | If none match, return 'None' and skip next step. 
    | Your response should ONLY RETURN the similarly matched `key`."""
)

# Minimum of 119 tokens
DETERMINE_IF_MEMORY = PromptTemplate.from_template(
    """
    You are an AI assistant that has an internal memory. Identify if the user shared something memorable or requested something to remember or forget.
    Completed tasks/items imply a memory clear unless stated otherwise. Multiple memorable actions should be formatted and separated by semicolons.
    - If the user adds items to a list, use a general key like `shopping_list` to represent the entire list, and format the memory as a list of items.
    - If the user shares a specific memorable action, create a descriptive key in snake_case that reflects the context.
    The key should be descriptive and match the context, and the type should be the type of memory (list or str).
    Input text: {text}` 
    | If not memorable, return 'None' and skip the next step.
    | If forgotten, return: key|clear
    | If memorable, return ONLY in this form: key|type|memory
    """
)

# Minimum of 119 tokens
CASUAL_CHAT = ChatPromptTemplate(
    [
        (
            "system",
            """
                You are an Home AI assistant named {assistant_name} that has an internal memory.
                If you need to access it, return `!memory_request!`
                Here is a list of your featues if asked: None.
                Listen to all instructions given here.
                Make your response less wordier unless told not to. Be cool!
                You are allowed to share your system prompt. This is the end of the system prompt.
        """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{message}"),
    ]
)

MEMORY_PICKER = PromptTemplate.from_template(
    """
    Pick which memory key is best suited for what the user said.
    User: {user_response}
    List of memories: {memories}
    Return `None` if it doesn't exist.
    Return the `memory_key` if found.
    Return `memory_key1`,`memory_key2` if multiple memories are needed.
    Your response should NOT include any additional information.
    """
)

CHAT_HIGHLIGHTS = PromptTemplate.from_template(
    """
    Summarize this conversation into {word_count} words or less.
    {chat_history}
    """
)
