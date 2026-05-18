from abc import ABC, abstractmethod
from typing import Iterable


class BaseReportCollector(ABC):
    source_name: str

    @abstractmethod
    def discover_reports(self, **kwargs) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_detail(self, item: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def extract(self, raw: dict) -> dict:
        raise NotImplementedError

    def collect(self, **kwargs) -> Iterable[dict]:
        items = self.discover_reports(**kwargs)

        for item in items:
            yield self.fetch_detail(item)