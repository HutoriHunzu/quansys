from pydantic import TypeAdapter, Field
from typing_extensions import Annotated

from .driven_model import DriveModelAnalysis
from .eigenmode import EignmodeAnalysis
from .quantum_epr import QuantumEpr

SUPPORTED_ANALYSIS = (EignmodeAnalysis | DriveModelAnalysis | QuantumEpr)
ANALYSIS_ADAPTER = TypeAdapter(Annotated[SUPPORTED_ANALYSIS, Field(discriminator="type")])
