from src.pysubmit.simulation.config_handler import ValuedVariable
from ansys.aedt.core import Hfss
from typing import List
from .constants import ROUNDING_DIGITS
import numpy as np
from functools import partial

from pint import UnitRegistry

# Create a unit registry
ureg = UnitRegistry()


def convert_to_si(value: float | int, unit: str = None) -> float:
    """
    Convert a value with its unit (as a tuple) to SI units.

    Args:
        value (tuple): A tuple containing the value (float or int) and the unit (str or None).
        unit (str)

    Returns:
        float: The value converted to SI units, or the original value if unitless.
    """

    if not unit or unit == '':  # If unit is None or an empty string, return the value as is
        return value

    try:
        quantity = value * ureg.Unit(unit)  # Create a Pint Quantity
        si_quantity = quantity.to_base_units()  # Convert to SI base units
        return si_quantity.magnitude  # Return the numeric value
    except Exception as e:
        raise ValueError(f"Error in conversion: {e}")


def set_variables(hfss: Hfss, values: List[ValuedVariable] | None):
    if values is None:
        return
    helper = partial(set_variable, hfss)
    list(map(helper, values))


def set_variable(hfss: Hfss, value: ValuedVariable):
    current_value = get_variable(hfss, value.name)
    new_value = round(convert_to_si(value.value, value.unit), ROUNDING_DIGITS)
    if not np.isclose(current_value, new_value):
        hfss[value.name] = value.to_string()


def get_variable(hfss: Hfss, variable_name):
    return round(hfss.get_evaluated_value(variable_name), ROUNDING_DIGITS)
