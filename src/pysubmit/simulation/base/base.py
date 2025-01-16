from pydantic import BaseModel, BeforeValidator, RootModel
from typing_extensions import Annotated, Generic, TypeVar
from abc import ABC, abstractmethod
from enum import StrEnum, auto


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


LIST_STR_TYPE = Annotated[list[str], BeforeValidator(ensure_list)]


class BaseResult(RootModel[dict], ABC):

    @abstractmethod
    def flatten(self) -> dict[str | bool | float, str | bool | float]:
        pass


class SupportedAnalysisNames(StrEnum):
    DRIVEN_MODEL = auto()
    EIGENMODE = auto()
    QUANTUM_EPR = auto()


class BaseAnalysis(BaseModel, ABC):
    type: SupportedAnalysisNames
    design_name: str

    @abstractmethod
    def analyze(self, **kwargs) -> BaseResult:
        pass

    # @abstractmethod
    # def format(self, **kwargs) -> dict:
    #     pass

    def analyze_and_extract_results(self, **kwargs) -> dict:
        results = self.analyze(**kwargs)  # should be a dict
        parameters = self.extract_parameters()

        return {'results': results,
                'setup': parameters}

    def extract_parameters(self) -> dict:
        return self.model_dump()




# class Solution(BaseModel):
#     setup: BaseAnalysis
#
#     pass
