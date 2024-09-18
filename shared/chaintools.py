from langchain_core.messages import AIMessage

def text(msg: AIMessage | str) -> str:
    if type(msg) is str:
        return msg
    if hasattr(msg, 'content'):
        return getattr(msg, 'content')