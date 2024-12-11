from pydantic import BaseModel
from typing import List

from pydantic import ValidationError
import yaml

from .junction_scheme import ConfigJunction
from .project_scheme import ConfigProject
from .variable_scheme import ValuedVariable
from .modes_labels_scheme import ModesAndLabels


class Config(BaseModel):
    config_project: ConfigProject
    junctions: List[ConfigJunction]
    modes_and_labels: List[ModesAndLabels]
    hfss_variables: List[ValuedVariable] = None


def load(config_path) -> Config:
    with open(config_path, "r") as file:
        config_data = yaml.safe_load(file)
    return Config(**config_data)


# def save():
#     pass
