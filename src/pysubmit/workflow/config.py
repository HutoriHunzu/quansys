from pydantic import BaseModel

from .builder import SUPPORTED_BUILDERS
from .sweep import SUPPORTED_SWEEPS
from .session_handler import SessionParameters
from .data_handler import DataHandler
from ..simulation import SUPPORTED_ANALYSIS

from pydantic_yaml import to_yaml_file, parse_yaml_file_as
from pathlib import Path

from pydantic import BeforeValidator
from typing_extensions import Annotated

def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value

BUILDER_SWEEP_TYPE = Annotated[list[SUPPORTED_SWEEPS], BeforeValidator(ensure_list)]



class WorkflowConfig(BaseModel):
    session_parameters: SessionParameters

    simulations: list[SUPPORTED_ANALYSIS]
    data_handler: DataHandler

    # builder phase
    builder: SUPPORTED_BUILDERS | None = None
    builder_sweep: BUILDER_SWEEP_TYPE | None = None

    # simulation
    # setup_sweep: SUPPORTED_SWEEPS | None = None

    def save_to_yaml(self, path: str | Path):
        to_yaml_file(path, self, map_indent=4)

    @classmethod
    def load_from_yaml(cls, path: str | Path):
        return parse_yaml_file_as(cls, path)


