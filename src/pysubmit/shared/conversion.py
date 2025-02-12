import pint

# Create a global unit registry to be used by the convert() function.
ureg = pint.UnitRegistry(case_sensitive=False)
ureg.formatter.default_format = "~"


def is_dimensionless(unit: str | None) -> bool:
    """
    Check whether the provided unit is considered dimensionless.

    Args:
        unit (str): A unit string.

    Returns:
        bool: True if the unit is None or empty (after stripping whitespace), False otherwise.
    """
    return not unit or unit.strip() == ''


class SIConverter:
    """
    A converter for handling conversions to and from SI (base) units.

    Provides:
      - convert_to: Converts a value with a given unit to SI base units.
      - convert_from: Converts a value assumed to be in SI to a desired target unit.

    In both methods, if the provided unit is None or empty, the value is assumed to be dimensionless
    and is returned unchanged (with an empty unit string).
    """

    @staticmethod
    def convert_to(value: float | int, unit: str) -> tuple[float, str]:
        """
        Convert a value from an arbitrary unit to SI base units.

        Args:
            value (float or int): The numeric value.
            unit (str): The unit of the value.
                        If None or empty, the value is treated as dimensionless.

        Returns:
            tuple: (converted_value, si_unit). For dimensionless inputs, returns (value, '').

        Raises:
            ValueError: If the quantity cannot be constructed.
        """
        try:
            # Create the quantity and convert it to SI (base) units.
            quantity = ureg.Quantity(value, unit)
            si_quantity = quantity.to_base_units()
        except Exception as e:
            raise ValueError(f"Error converting {value} from unit '{unit}' to SI: {e}")
        return si_quantity.magnitude, str(si_quantity.units)

    @staticmethod
    def convert_from(value: float | int, target_unit: str) -> tuple[float, str]:
        """
        Convert a value assumed to be in SI base units to a specified target unit.

        Args:
            value (float or int): The numeric value (assumed to be in SI).
            target_unit (str): The desired target unit.
                               If None or empty, the value is treated as dimensionless.

        Returns:
            tuple: (converted_value, target_unit). For dimensionless targets, returns (value, '').

        Raises:
            ValueError: If the conversion cannot be performed.
        """
        try:
            # Determine the SI base unit corresponding to the target unit.
            base_unit = ureg.Quantity(1, target_unit).to_base_units().units
        except Exception as e:
            raise ValueError(f"Error determining SI base unit for target '{target_unit}': {e}")
        try:
            # Create a quantity in SI using the determined base unit and convert it.
            quantity = ureg.Quantity(value, base_unit)
            converted_quantity = quantity.to(target_unit)
        except Exception as e:
            raise ValueError(f"Error converting from SI to target unit '{target_unit}': {e}")
        return converted_quantity.magnitude, str(converted_quantity.units)


def convert(value: float | int, unit: str, target_unit: str | None) -> tuple[float, str]:
    """
    Convert a value from one arbitrary unit to another directly.

    This function does not rely on the SIConverter class. Instead, it creates a Pint quantity
    from the given value and unit and uses the `.to()` method to perform the conversion.

    Args:
        value (float or int): The numeric value.
        unit (str): The original unit of the value.
                    If None or empty, the value is assumed to be dimensionless.
        target_unit (str): The desired target unit.
                           If None or empty, no conversion is performed.

    Returns:
        tuple: (converted_value, unit_str). For dimensionless inputs or targets, returns (value, '').

    Raises:
        ValueError: If the conversion fails.
    """
    if target_unit is None or target_unit == '':
        return value, unit

    if is_dimensionless(unit):
        # Input is dimensionless; nothing to convert.
        return value, ''
    try:
        quantity = ureg.Quantity(value, unit)
        converted_quantity = quantity.to(target_unit)
    except Exception as e:
        raise ValueError(f"Error converting {value} from '{unit}' to '{target_unit}': {e}")
    return converted_quantity.magnitude, str(converted_quantity.units)


# === Example Usages ===

if __name__ == "__main__":
    # Using the SIConverter class:
    converter = SIConverter()

    # Example 1: Convert 10 meters (given in arbitrary unit) to SI.
    si_value, si_unit = converter.convert_to(10, "meter")
    print(f"10 meter -> SI: {si_value} {si_unit}")  # e.g., 10.0 meter

    # Example 2: Convert 10 SI (meters) to inches.
    inch_value, inch_unit = converter.convert_from(10, "inch")
    print(f"10 SI (meters) -> inch: {inch_value} {inch_unit}")

    # Using the standalone convert() function:

    # Example 3: Convert 3.5 inches to centimeters.
    cm_value, cm_unit = convert(3.5, "inch", "centimeter")
    print(f"3.5 inch -> centimeter: {cm_value} {cm_unit}")

    # Example 4: Dimensionless conversion (no conversion performed).
    value_dimless, unit_dimless = convert(42, "", "any_unit")
    print(f"42 (dimensionless) -> any_unit: {value_dimless} '{unit_dimless}'")

    # Example 5: Convert 3.5 inches to centimeters.
    cm_value, cm_unit = convert(3.5, "Hz", "GHz")
    print(f"3.5 inch -> centimeter: {cm_value} {cm_unit}")


