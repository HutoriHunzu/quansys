from pydantic import Field
from .base import BaseBuilder, BuildInterface, HDF5Handler
from typing import Literal, Callable, Iterable

from ansys.aedt.core.hfss import Hfss


class FunctionBuilder(BaseBuilder):
    type: Literal['function_builder'] = 'function_builder'
    function: Callable[[Hfss, ...], Iterable[dict]]
    args: dict = Field(default_factory=dict)

    def build(self, hfss: Hfss, data_handler: HDF5Handler | None = None,
              parameters: dict | None = None) -> Iterable[BuildInterface]:
        kwargs = {'data_handler': data_handler}
        combined_args = dict(**self.args, **kwargs)

        builder_interface_generator = self.function(hfss, **combined_args)

        for elem in builder_interface_generator:
            yield BuildInterface(
                **elem
            )
