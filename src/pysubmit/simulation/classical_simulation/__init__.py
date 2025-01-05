from .eigenmode import EignModeAnalysis
from .driven_model import DriveModelAnalysis

from pydantic import TypeAdapter, Field
from typing_extensions import Annotated

SUPPORTED_ANALYSIS = (EignModeAnalysis | DriveModelAnalysis)
ANALYSIS_ADAPTER = TypeAdapter(Annotated[SUPPORTED_ANALYSIS, Field(discriminator="type")])
