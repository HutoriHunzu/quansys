from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from abc import ABC, abstractmethod
from enum import StrEnum, auto


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


LIST_STR_TYPE = Annotated[list[str], BeforeValidator(ensure_list)]

class SupportedAnalysisNames(StrEnum):
    DRIVEN_MODEL = auto()
    EIGENMODE = auto()
    QUANTUM_EPR = auto()



class BaseAnalysis(BaseModel, ABC):
    type: SupportedAnalysisNames
    design_name: str

    @abstractmethod
    def analyze(self, **kwargs) -> dict:
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
        return dict(self)


# class Solution(BaseModel):
#     setup: BaseAnalysis
#
#     pass
