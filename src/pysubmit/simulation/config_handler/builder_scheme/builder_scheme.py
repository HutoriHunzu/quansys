from pydantic import BaseModel
from typing import Literal, Iterable
from ..variable_scheme import Variable, ValuedVariable, ConfigSweep

from .designs import two_mode_srf_cavity
from typing import Generator

SUPPORTED_BUILDERS = ()


class TwoModesCavity(BaseModel):
    type: Literal['two_mode_srf_cavity']
    design_name: str

    sweep: ConfigSweep | None

    def build(self, hfss) -> Generator[dict, None, None]:
        for variables in self.prepare_variables():
            yield two_mode_srf_cavity.build(hfss,
                                            self.design_name,
                                            cavity_params=variables)

    def prepare_variables(self) -> Iterable[dict]:

        if self.sweep is None:
            return [{}]

        generator = self.sweep.generate_variation()
        return map(ValuedVariable.iterable_to_dict, generator)


class ConfigBuilder(BaseModel):
    builder: TwoModesCavity | None = None

    def build(self, hfss) -> Iterable[dict]:
        if self.builder is None:
            return [{}]

        return self.builder.build(hfss)
