from abc import ABC, abstractmethod
from typing import Any, Iterable


class BaseCollector(ABC):
    source_name: str

    @abstractmethod
    def collect(self, **kwargs) -> Iterable[Any]:
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw: Any) -> dict:
        raise NotImplementedError

    @abstractmethod
    def extract(self, parsed: dict) -> dict:
        raise NotImplementedError