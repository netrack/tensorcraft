import io

from abc import ABCMeta, abstractmethod
from typing import Sequence

from polynome.model import Model


class AbstractStorage(metaclass=ABCMeta):

    @abstractmethod
    async def all(self) -> Sequence[Model]:
        pass

    @abstractmethod
    async def save(self, name: str, tag: str, stream: io.IOBase) -> Model:
        pass

    @abstractmethod
    async def delete(self, name: str, tag: str) -> None:
        pass

    @abstractmethod
    async def load(self, name: str, tag: str) -> Model:
        pass

    @abstractmethod
    async def export(self, name: str, tag: str) -> io.IOBase:
        pass
