from pydantic import TypeAdapter, Field
from typing_extensions import Annotated

from .driven_model import DriveModelAnalysis
from .eigenmode import EigenmodeAnalysis, EigenmodeResults
from .quantum_epr import QuantumEPR, QuantumResults
from .base import SimulationTypesNames, BaseSimulationOutput, BaseAnalysis

SUPPORTED_ANALYSIS = Annotated[
    EigenmodeAnalysis | DriveModelAnalysis | QuantumEPR,
    Field(discriminator="type")
]
ANALYSIS_ADAPTER = TypeAdapter(SUPPORTED_ANALYSIS)

SUPPORTED_RESULTS = Annotated[
    EigenmodeResults | QuantumResults,
    Field(discriminator="type")
]
SIMULATION_RESULTS_ADAPTER = TypeAdapter(SUPPORTED_RESULTS)

__all__ = [
    "DriveModelAnalysis",
    "EigenmodeAnalysis",
    "EigenmodeResults",
    "QuantumEPR",
    "QuantumResults",
    "SimulationTypesNames",
    "BaseSimulationOutput",
    "BaseAnalysis",
    "SUPPORTED_ANALYSIS",
    "ANALYSIS_ADAPTER",
    "SUPPORTED_RESULTS",
    "SIMULATION_RESULTS_ADAPTER",
]
