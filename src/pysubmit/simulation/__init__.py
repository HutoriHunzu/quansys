from pydantic import TypeAdapter, Field
from typing_extensions import Annotated

from .driven_model import DriveModelAnalysis
from .eigenmode import EignmodeAnalysis
from .quantum_epr import QuantumEpr
from .base import SupportedAnalysisNames

SUPPORTED_ANALYSIS = Annotated[EignmodeAnalysis | DriveModelAnalysis | QuantumEpr, Field(discriminator='type')]
ANALYSIS_ADAPTER = TypeAdapter(SUPPORTED_ANALYSIS)
