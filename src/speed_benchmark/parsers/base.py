# src/speed_benchmark/parsers/base.py
from abc import ABC, abstractmethod


class BaseParser(ABC):
    name: str

    @abstractmethod
    def parse(self, path: str) -> str: ...

    def is_available(self) -> bool:
        return True
