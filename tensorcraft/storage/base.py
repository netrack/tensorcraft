import io
import pathlib

from abc import ABCMeta, abstractmethod
from typing import Sequence

from tensorcraft.model import Model


class AbstractStorage(metaclass=ABCMeta):

    @property
    @abstractmethod
    async def root_path(self) -> pathlib.Path:
        """Root path of the storage.

        The returned path specifies the path where all models and related
        metadata is persisted.

        Returns:
            Data root path as :class:`pathlib.Path`.
        """
        pass

    @abstractmethod
    async def all(self) -> Sequence[Model]:
        """List all existing models.

        The returned models are not necessary loaded for the sake of
        performance.

        Returns:
            Sequence of :class:`Model`.
        """
        pass

    @abstractmethod
    async def save(self, name: str, tag: str, stream: io.IOBase) -> Model:
        """Save the model archive.

        The persistence guarantee is provided by the implementation.

        Args:
            name (str): Model name.
            tag (str): Model tag.

        Returns:
            Saved instance of :class:`Model`.
        """
        pass

    @abstractmethod
    async def delete(self, name: str, tag: str) -> None:
        """Delete the model.

        After the deletion model should not be addressable anymore.

        Args:
            name (str): Model name.
            tag (str): Model tag.
        """
        pass

    @abstractmethod
    async def load(self, name: str, tag: str) -> Model:
        """Load the model.

        Load model into the memory from the storage. Implementation must
        consider concurrent requests to load the same model.

        Args:
            name (str): Model name.
            tag (str): Model tag.

        Returns:
            Loaded :class:`Model`.
        """
        pass

    @abstractmethod
    async def export(self, name: str, tag: str, writer: io.IOBase) -> None:
        """Export model to the writer

        Write model's archive into the stream. Implementation must consider
        concurrent requests to export the same model.

        Args:
            name (str): Model name
            tag (str): Model tag
            writer (io.IOBase): Destination writer instance.
        """
        pass
