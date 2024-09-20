from dataclasses import dataclass
from typing import Callable

@dataclass
class ResponseMixin:
    response: str
    completed: bool = False
    retry: bool = False
    meta: dict | None = None
    helper: Callable | None = None


    def from_retry(cls, response):
        return cls(response=response, retry=True)

