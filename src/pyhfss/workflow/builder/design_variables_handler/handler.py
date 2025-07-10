from ....shared.variables_types import GenericValue, Value
from ansys.aedt.core import Hfss
from typing import Iterable
from functools import partial
from pydantic import TypeAdapter

SupportedInputType = dict[str, GenericValue | Value]
InputAdapter = TypeAdapter(SupportedInputType)


def set_variables(hfss: Hfss, variables: SupportedInputType):
    if variables is None or variables == {}:
        return

    instance = InputAdapter.validate_python(variables)
    for k, v in instance.items():
        set_variable(hfss, k, v.to_str())


def set_variable(hfss: Hfss, name: str, value: str):
    hfss[name] = value


def get_variable(hfss: Hfss, variable_name):
    return hfss.get_evaluated_value(variable_name)
