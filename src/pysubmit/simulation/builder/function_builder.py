from pydantic import Field
from .base import BaseBuilder
from typing import Literal, Callable, Iterable

from .builder_interface import BuildInterface
from ansys.aedt.core.hfss import Hfss


class FunctionBuilder(BaseBuilder):
    type: Literal['function_builder'] = 'function_builder'
    function: Callable[[Hfss, ...], Iterable[dict]]
    args: dict = Field(default_factory=dict)

    def build(self, hfss, data_handler) -> Iterable[BuildInterface]:
        kwargs = {'data_handler': data_handler}
        combined_args = dict(**self.args, **kwargs)

        builder_interface_generator = self.function(hfss, **combined_args)

        for elem in builder_interface_generator:
            yield BuildInterface(
                **elem
            )
