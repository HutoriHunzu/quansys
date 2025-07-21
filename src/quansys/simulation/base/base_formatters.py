from abc import ABC, abstractmethod

from pydantic import BaseModel, RootModel
from typing_extensions import TypeVar, Generic


class BaseResult(RootModel[dict], ABC):

    # @abstractmethod
    # def to_dict(self) -> dict:
    #     pass

    @abstractmethod
    def flatten(self) -> dict[str | bool | float, str | bool | float]:
        pass


TResult = TypeVar('TResult', bound='BaseResult')

class BaseFormatter(BaseModel, Generic[TResult], ABC):

    @abstractmethod
    def format(self, setup) -> TResult:
        pass

    @abstractmethod
    def load(self, data: dict) -> TResult:
        pass