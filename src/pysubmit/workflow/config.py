from pydantic import BaseModel

from .builder import SUPPORTED_BUILDERS
from .sweep import SUPPORTED_SWEEPS
from .session_handler import SessionParameters
from .data_handler import DataParameters
from ..simulation import SUPPORTED_ANALYSIS


class WorkflowConfig(BaseModel):
    session_parameters: SessionParameters

    simulations: list[SUPPORTED_ANALYSIS]
    data_parameters: DataParameters

    # builder phase
    builder: SUPPORTED_BUILDERS | None = None
    builder_sweep: SUPPORTED_SWEEPS | None = None

    # simulation
    # setup_sweep: SUPPORTED_SWEEPS | None = None


