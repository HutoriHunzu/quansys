from pydantic import Field
from .base import BaseBuilder, DataHandler
from typing import Literal, Callable, Iterable

from ansys.aedt.core.hfss import Hfss


class FunctionBuilder(BaseBuilder):
    type: Literal['function_builder'] = 'function_builder'
    function: Callable[[Hfss, ...], dict] = Field(..., exclude=True)
    args: dict = Field(default_factory=dict)

    def build(self, hfss: Hfss,
              data_handler: DataHandler | None = None,
              parameters: dict | None = None) -> dict:
        # data_handler: HDF5Handler | None = None,
        # kwargs = {'data_handler': data_handler}
        parameters = parameters or {}
        combined_args = dict(**self.args, **parameters)

        return self.function(hfss, **combined_args)
