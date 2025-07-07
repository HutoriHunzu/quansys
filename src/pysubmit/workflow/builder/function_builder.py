from pydantic import Field
from .base import BaseBuilder, DataHandler
from typing import Literal, Callable, Iterable
from ..sweep.utils import merge_dicts


from ansys.aedt.core.hfss import Hfss


class FunctionBuilder(BaseBuilder):
    type: Literal['function_builder'] = 'function_builder'
    function: Callable[[Hfss, ...], dict] = Field(..., exclude=True)
    args: dict = Field(default_factory=dict)

    def build(self, hfss: Hfss,
              parameters: dict | None = None) -> dict:

        parameters = parameters or {}
        combined_args = merge_dicts(self.args, parameters)

        return self.function(hfss, **combined_args)
