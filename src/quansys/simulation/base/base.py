from pydantic import BaseModel, TypeAdapter
from abc import ABC, abstractmethod
from enum import StrEnum, auto
from ansys.aedt.core import Hfss

FlatDictType = dict[str, str | bool | float]
FlatDictAdapter = TypeAdapter(FlatDictType)


class SupportedSetupTypes:
    EIGENMODE = 'HfssEigen'


class SimulationTypesNames(StrEnum):
    DRIVEN_MODEL = auto()
    EIGENMODE = auto()
    QUANTUM_EPR = auto()


class SimulationOutputTypesNames(StrEnum):
    EIGENMODE_RESULT = auto()
    QUANTUM_EPR_RESULT = auto()


class BaseSimulationOutput(BaseModel, ABC):
    type: SimulationOutputTypesNames

    @abstractmethod
    def flatten(self) -> dict:
        pass


class BaseAnalysis(BaseModel, ABC):
    type: SimulationTypesNames

    @abstractmethod
    def analyze(self, hfss: Hfss) -> BaseSimulationOutput:
        pass
