from dataclasses import dataclass

@dataclass
class ResponseMixin:
    response: str
    completed: bool = False
    retry: bool = False
    meta: dict | None = None


    def from_retry(self, response):
        return self.__class__(response=response, retry=True)

