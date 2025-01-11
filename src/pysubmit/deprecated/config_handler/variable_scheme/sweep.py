from pydantic import BaseModel, TypeAdapter
from typing import List, Iterable
from abc import abstractmethod
from .valued_variable import ValuedVariable, Variable

from .sweep_types import ZipSweep, ProductSweep

SUPPORTED_SWEEPS = (ZipSweep | ProductSweep)
SWEEP_ADAPTER = TypeAdapter(SUPPORTED_SWEEPS)


class ConfigSweep(BaseModel):
    name: str
    args: dict

    def generate_variation(self, **runtime_data) -> Iterable[Iterable[ValuedVariable]]:
        sweep_data = dict({'type': self.name}, **self.args)
        sweep = SWEEP_ADAPTER.validate_python(sweep_data)

        return sweep.gen(**runtime_data)
