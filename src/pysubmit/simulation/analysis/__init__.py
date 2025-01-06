from pydantic import TypeAdapter, Field
from typing_extensions import Annotated

from .driven_model import DriveModelAnalysis
from .eigenmode import EignModeAnalysis
from .quantum_epr import QuantumEpr

SUPPORTED_ANALYSIS = (EignModeAnalysis | DriveModelAnalysis | QuantumEpr)
ANALYSIS_ADAPTER = TypeAdapter(Annotated[SUPPORTED_ANALYSIS, Field(discriminator="type")])
