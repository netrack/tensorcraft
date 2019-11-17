import uuid

from abc import ABCMeta, abstractmethod
from typing import Dict, NamedTuple, Sequence, Union


class Metric(NamedTuple):
    """Metric of the model's training."""

    name: str
    value: float

    def __repr__(self) -> str:
        return f"<Metric {self.name} value={self.value}>"

    @classmethod
    def from_dict(cls, **kwargs):
        return cls(**kwargs)

    def asdict(self) -> Dict:
        return dict(name=self.name, value=self.value)


class Epoch(NamedTuple):
    """Epoch is an iteration of model fitting (training).

    Attributes:
        metrics -- list of model's metrics
    """

    metrics: Sequence[Metric]

    @classmethod
    def new(cls, metrics=Sequence[Dict]):
        return cls([Metric.from_dict(**m) for m in metrics])

    @classmethod
    def from_dict(cls, **kwargs):
        return cls([Metric.from_dict(**m) for m in kwargs.pop("metrics", [])])

    def asdict(self) -> Dict:
        return dict(metrics=[m.asdict() for m in self.metrics])


class Experiment:
    """Machine-learning experiment.

    Attributes:
        id -- unique experiment identifier
        name -- name of the experiment
        epochs -- a list of experiment epochs
    """

    @classmethod
    def new(cls, name: str, epochs=Sequence[Dict]) -> 'Experiment':
        experiment_id = uuid.uuid4()
        epochs = [Epoch.from_dict(**e) for e in epochs]
        return cls(uid=experiment_id, name=name, epochs=epochs)

    @classmethod
    def from_dict(cls, **kwargs) -> 'Experiment':
        epochs = [Epoch.from_dict(**e) for e in kwargs.pop("epochs", [])]
        return cls(epochs=epochs, **kwargs)

    def __init__(self,
                 uid: Union[uuid.UUID, str],
                 name: str,
                 epochs: Sequence[Epoch]):
        self.id = uuid.UUID(str(uid))
        self.name = name
        self.epochs = epochs

    def __repr__(self) -> str:
        return (f"<Experiment {self.name} id={self.id} "
                f"epochs={len(self.epochs)}>")

    def asdict(self) -> Dict:
        return dict(id=self.id.hex,
                    name=self.name,
                    epochs=[e.asdict() for e in self.epochs])


class AbstractStorage(metaclass=ABCMeta):
    """Storage used to persist experiments."""

    @abstractmethod
    async def save(self, e: Experiment) -> None:
        """Save the experiment.

        The persistence guarantee is defined by the implementation.
        """

    @abstractmethod
    async def save_epoch(self, name: str, epoch: Epoch) -> None:
        """Save the epoch with metrics.

        Add a new epoch to the experiment, after execution count of epochs
        for the experiment referenced by eid should be increased by one.

        Args:
            name -- experiment name
            epoch -- experiment epoch
        """

    @abstractmethod
    async def load(self, name: str) -> Experiment:
        """Load the experiment.

        Args:
            name -- experiment name
        """

    @abstractmethod
    async def all(self) -> Sequence[Experiment]:
        """Load all experiments."""
