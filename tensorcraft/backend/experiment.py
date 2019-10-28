import uuid

from abc import ABCMeta, abstractmethod
from typing import NamedTuple, Sequence, Union


class Metric(NamedTuple):
    """Metric of the model's training."""

    name: str
    value: float

    def __repr__(self) -> str:
        return f"<Metric {self.name} value={self.value}>"


class Epoch:
    """Epoch is an iteration of model fitting (training).

    Attributes:
        id -- unique epoch identifier
        metrics -- list of model's metrics
    """

    def __init__(self,
                 uid: Union[uuid.UUID, str],
                 metrics: Sequence[Metric]):
        self.id = uuid.UUID(str(uid))
        self.metrics = metrics


class Experiment:
    """Machine-learning experiment.

    Attributes:
        id -- unique experiment identifier
        name -- name of the experiment
    """

    @classmethod
    def new(cls, name: str, **kwargs) -> 'Experiment':
        experiment_id = uuid.uuidv4()
        return cls(uid=experiment_id, name=name, **kwargs)

    def __init__(self,
                 uid: Union[uuid.UUID, str],
                 name: str,
                 epochs: Sequence[Epoch]):
        self.id = uuid.UUID(str(uid))
        self.name = name

    def todict(self):
        return dict(id=self.id.hex,
                    name=self.name)


class AbstractStorage(metaclass=ABCMeta):
    """Storage used to persist experiments."""

    @abstractmethod
    async def save(self, e: Experiment) -> None:
        """Save the experiment.

        The persistence guarantee is defined by the implementation.
        """
