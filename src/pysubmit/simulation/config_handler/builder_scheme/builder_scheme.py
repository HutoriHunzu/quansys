from pydantic import BaseModel
from typing import Literal, Iterable
from ..variable_scheme import Variable, ValuedVariable, ConfigSweep

from .designs import two_mode_srf_cavity

SUPPORTED_BUILDERS = ()


class TwoModesCavity(BaseModel):
    type: Literal['two_mode_srf_cavity']
    build_design_name: str
    dst_design_name: str

    sweep: ConfigSweep | None

    def build(self, hfss):
        for variables in self.prepare_variables():
            return two_mode_srf_cavity.build(hfss,
                                             self.build_design_name,
                                             self.dst_design_name,
                                             cavity_params=variables)

    def prepare_variables(self) -> Iterable[dict]:

        if self.sweep is None:
            return [{}]

        generator = self.sweep.generate_variation()
        return map(ValuedVariable.list_to_dict, generator)


class ConfigBuilder(BaseModel):
    builder: TwoModesCavity | None = None

    def build(self, hfss) -> dict:
        if self.builder is None:
            return {}

        return self.builder.build(hfss)
