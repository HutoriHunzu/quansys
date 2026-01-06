from pint import UnitRegistry

# Create a unit registry
ureg = UnitRegistry()


def convert_from_si(value, to_unit):
    """
    Convert a value from SI units to a specified unit.

    Args:
        value (float): The numeric value in SI units.
        to_unit (str): The unit to convert to.

    Returns:
        float: The converted value.
    """
    if to_unit == "":
        return value

    # Create a quantity in SI base units (assume it's already in SI)
    quantity = value * ureg.dimensionless

    # Convert to the desired unit
    converted_quantity = quantity.to(to_unit)

    return converted_quantity


def convert_to_si(value: float | int, unit: str = None) -> float:
    """
    Convert a value with its unit (as a tuple) to SI units.

    Args:
        value (tuple): A tuple containing the value (float or int) and the unit (str or None).
        unit (str)

    Returns:
        float: The value converted to SI units, or the original value if unitless.
    """

    if (
        not unit or unit == ""
    ):  # If unit is None or an empty string, return the value as is
        return value

    try:
        quantity = value * ureg.Unit(unit)  # Create a Pint Quantity
        si_quantity = quantity.to_base_units()  # Convert to SI base units
        return si_quantity.magnitude  # Return the numeric value
    except Exception as e:
        raise ValueError(f"Error in conversion: {e}")
