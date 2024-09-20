def text(msg: object) -> str:
    if type(msg) is str:
        return msg
    if hasattr(msg, 'content'):
        return getattr(msg, 'content')