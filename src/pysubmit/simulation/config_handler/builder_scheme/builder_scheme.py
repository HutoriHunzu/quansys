from pydantic import BaseModel
from typing import Literal, Iterable

from ..project_scheme import ConfigProject
from ..variable_scheme import Variable, ValuedVariable, ConfigSweep

from .designs import two_mode_srf_cavity
from typing import Generator

SUPPORTED_BUILDERS = ()


class TwoModesCavity(BaseModel):
    type: Literal['two_mode_srf_cavity']

    sweep: ConfigSweep | None

    def build(self, hfss, config_project: ConfigProject) -> Generator[dict, None, None]:
        for variables in self.prepare_variables():
            yield two_mode_srf_cavity.build(hfss,
                                            config_project,
                                            cavity_params=variables)

    def prepare_variables(self) -> Iterable[dict]:

        if self.sweep is None:
            return [{}]

        generator = self.sweep.generate_variation()
        return map(ValuedVariable.iterable_to_dict, generator)


class ConfigBuilder(BaseModel):
    builder: TwoModesCavity | None = None

    def build(self, hfss, config_project: ConfigProject) -> Iterable[dict]:
        if self.builder is None:
            return [{}]

        return self.builder.build(hfss, config_project)
