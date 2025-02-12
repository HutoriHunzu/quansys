from pydantic import BaseModel, BeforeValidator, RootModel, TypeAdapter
from typing import Literal, Self
from abc import ABC, abstractmethod
from enum import StrEnum, auto
import json


FlatDictType = dict[str, str | bool | float]
FlatDictAdapter = TypeAdapter(FlatDictType)


class SupportedSetupTypes:
    EIGENMODE = 'HfssEigen'


class SupportedAnalysisNames(StrEnum):
    DRIVEN_MODEL = auto()
    EIGENMODE = auto()
    QUANTUM_EPR = auto()



class JsonSerializable(ABC):

    @abstractmethod
    def serialize(self) -> dict:
        """ should be compatible with json encoding"""
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: dict) -> Self:
        pass


class FlatDictClass(ABC):

    @abstractmethod
    def flatten(self) -> FlatDictType:
        pass


class BaseResult(BaseModel, FlatDictClass, ABC):

    type: SupportedAnalysisNames

    def validate_flatten(self):
        FlatDictAdapter.validate_python(self.flatten())

    # def _validate_serialize(self):
    #     json.dumps(self.serialize())
    #
    # def validate(self):
    #     # self._validate_serialize()
    #     self._validate_flatten()



class BaseAnalysis(BaseModel, ABC):
    type: SupportedAnalysisNames

    @abstractmethod
    def analyze(self, **kwargs) -> BaseResult:
        pass

    # def serialize(self) -> dict:
    #     return self.model_dump()

    # @abstractmethod
    # def check_requirement(self):
    #     pass
