from ....shared.variables import ValuedVariable
from ansys.aedt.core import Hfss
from typing import Iterable
from functools import partial


def set_variables(hfss: Hfss, values: Iterable[ValuedVariable] | None):
    if values is None:
        return
    helper = partial(set_variable, hfss)
    list(map(helper, values))


def set_variable(hfss: Hfss, value: ValuedVariable):
    # current_value = get_variable(hfss, value.name)
    # current_value_in_units = convert_from_si(current_value, value.unit)
    # new_value = convert_to_si(value.value, value.unit)
    # if not np.isclose(current_value, new_value):
    hfss[value.name] = value.to_string()


def get_variable(hfss: Hfss, variable_name):
    return hfss.get_evaluated_value(variable_name)