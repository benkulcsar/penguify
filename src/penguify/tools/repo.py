from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type, TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class PydanticRepository(ABC):
    @abstractmethod
    def save(self, model: BaseModel) -> None: ...

    @abstractmethod
    def load(self, model_cls: Type[M]) -> M: ...


class JsonFilePydanticRepository(PydanticRepository):
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, model: BaseModel) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(model.model_dump_json(indent=2), encoding="utf-8")

    def load(self, model_cls: Type[M]) -> M:
        """Load a Pydantic model from the JSON file."""
        data = self.path.read_text(encoding="utf-8")
        return model_cls.model_validate_json(data)
