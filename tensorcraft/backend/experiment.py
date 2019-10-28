import uuid

from abc import ABCMeta, abstractmethod
from typing import Union


class Experiment:
    """Machine-learning experiment.
    
    Attributes:
        id -- unique experiment identifier
        name -- name of the experiment
    """

    @classmethod
    def new(cls, name: str) -> 'Experiment':
        experiment_id = uuid.uuidv4()

        return cls(id=experiment_id, name=name)

    def __init__(self,
                 uid: Union[uuid.UUID, str],
                 name: str):
        self.id = uuid.UUID(str(uid))
        self.name = name


class AbstractStorage(metaclass=ABCMeta):
    """Storage used to persist experiments."""

    @abstractmethod
    async def save(self, name: str) -> None:
        """Save the experiment.

        The persistence guaranteed is provided by the implementation.
        """
