from pydantic import BaseModel
from ...simulation import SUPPORTED_ANALYSIS


class SimulationConfig(BaseModel):
    gpus: int = 0
    cpus: int = 4

    # list of execution
    analysis: list[SUPPORTED_ANALYSIS]



