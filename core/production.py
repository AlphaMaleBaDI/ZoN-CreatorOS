from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Artifact:
    type: str = ""
    title: str = ""
    body: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProductionEngine(ABC):
    @abstractmethod
    def generate(self, candidate, understanding, artifact_type: str = "") -> Artifact:
        ...
