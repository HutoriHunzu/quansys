from pydantic import TypeAdapter, Field
from typing_extensions import Annotated

from .driven_model import DriveModelAnalysis
from .eigenmode import EigenmodeAnalysis
from .quantum_epr import QuantumEpr
from .base import SimulationTypesNames, BaseSimulationOutput, BaseAnalysis

SUPPORTED_ANALYSIS = Annotated[EigenmodeAnalysis | DriveModelAnalysis | QuantumEpr, Field(discriminator='type')]
ANALYSIS_ADAPTER = TypeAdapter(SUPPORTED_ANALYSIS)
