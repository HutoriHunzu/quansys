from pydantic import BaseModel
from typing import List

from pydantic import ValidationError
import yaml

from .junction_scheme import ConfigJunction
from .project_scheme import ConfigProject
from .session_config import SessionParameters
from .variable_scheme import ValuedVariable, ConfigSweep
from .modes_labels_scheme import ModesAndLabels
from .builder_scheme import ConfigBuilder
from ..builder import SUPPORTED_BUILDERS


class Config(BaseModel):
    name: str
    session_parameters: SessionParameters
    builder: SUPPORTED_BUILDERS

    junctions: List[ConfigJunction] | None = None
    modes_and_labels: List[ModesAndLabels] | None = None
    hfss_variables: List[ValuedVariable] | None = None
    sweep: ConfigSweep | None = None
    config_builder: ConfigBuilder | None = None


def load(config_path) -> Config:
    with open(config_path, "r") as file:
        config_data = yaml.safe_load(file)
    return Config.model_validate(config_data)


def save(config_path, config: Config):
    d = config.model_dump()

    with open(config_path, "w") as file:
        yaml.safe_dump(d, file)
