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
    EIGENMODE_REPORT = auto()
    QUANTUM_EPR_RESULT = auto()
    QUANTUM_EPR_REPORT = auto()
    # EIGENMODE_RESULT = auto()
    # EIGENMODE_RESULT = auto()
    # REPORT = auto()


# class SupportedResultsNames(StrEnum):
#     DRIVEN_MODEL_RESULT = auto()
#     EIGENMODE_RESULT = auto()
#     QUANTUM_EPR_RESULT = auto()
#
#
# class SupportedReportNames(StrEnum):
#     DRIVEN_MODEL_REPORT = auto()
#     EIGENMODE_REPORT = auto()
#     QUANTUM_EPR_REPORT = auto()
#

class BaseSimulationOutput(BaseModel, ABC):
    type: SimulationOutputTypesNames

    @abstractmethod
    def flatten(self) -> dict:
        pass

# class BaseReport(BaseModel, ABC):
#     id: str = ''
#     type: SimulationTypesNames
#
#     @abstractmethod
#     def flatten(self) -> dict:
#         pass

    # def _validate_serialize(self):
    #     json.dumps(self.serialize())
    #
    # def validate(self):
    #     # self._validate_serialize()
    #     self._validate_flatten()


class BaseAnalysis(BaseModel, ABC):
    type: SimulationTypesNames

    @abstractmethod
    def analyze(self, hfss: Hfss) -> BaseSimulationOutput:
        pass

    # def serialize(self) -> dict:
    #     return self.model_dump()

    # @abstractmethod
    # def check_requirement(self):
    #     pass
