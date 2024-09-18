from dataclasses import dataclass

@dataclass
class ResponseMixin:
    response: str
    completed: bool = False
    retry: bool = False
    meta: dict | None = None


    def from_retry(cls, response):
        return cls(response=response, retry=True)

