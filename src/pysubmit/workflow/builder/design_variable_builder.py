from .base import BaseBuilder, HDF5Handler, ValuedVariable
from typing import Literal, Iterable
from typing_extensions import Annotated
from pydantic import BeforeValidator
from ansys.aedt.core.hfss import Hfss

from .design_variables_handler import set_variables


# def ensure_list(value: list[str] | str) -> list[str]:
#     if not isinstance(value, list):
#         value = [value]
#     if len(value) < 1:
#         raise ValueError('must be provided with at least one string')
#     return value
#
#
# NAMES_TYPE = Annotated[list[str], BeforeValidator(ensure_list)]


class DesignVariableBuilder(BaseBuilder):
    type: Literal['design_variable_builder'] = 'design_variable_builder'
    design_name: str
    setup_name: str

    def build(self, hfss: Hfss,
              data_handler: HDF5Handler | None = None,
              parameters: list[ValuedVariable] = None):
        if parameters is None:
            return {}

        hfss.set_active_design(self.design_name)
        set_variables(hfss, parameters)
        return ValuedVariable.iterable_to_dict(parameters)
