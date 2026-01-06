"""
Tests for builder classes used to configure HFSS designs.

Covers:
- DesignVariableBuilder: sets design variables directly.
- FunctionBuilder: applies custom build logic via function.
- ModuleBuilder: dynamically imports user module and runs build function.

Includes both success and failure scenarios.
"""

import pytest
from quansys.workflow import DesignVariableBuilder, ModuleBuilder, FunctionBuilder


VARIABLE_TO_CHANGE = "chip_base_width"
VARIABLE_PLUS_ONE = f"{VARIABLE_TO_CHANGE}_plus_one_mm"


def test_design_variable_builder(simple_design):
    """Tests that DesignVariableBuilder sets parameters correctly in the HFSS design."""
    builder = DesignVariableBuilder(
        design_name="my_design",
    )

    builder.build(simple_design, parameters={VARIABLE_TO_CHANGE: "3mm"})

    assert simple_design[VARIABLE_TO_CHANGE] == "3mm"
    assert simple_design.evaluate_expression(simple_design[VARIABLE_PLUS_ONE]) == 0.004


def test_function_builder(simple_design):
    """Tests that FunctionBuilder executes the provided function correctly."""

    def builder_function(hfss, name_value_dict):
        for name, value in name_value_dict.items():
            hfss[name] = value

    builder = FunctionBuilder(function=builder_function)

    builder.build(
        hfss=simple_design, parameters={"name_value_dict": {VARIABLE_TO_CHANGE: "5mm"}}
    )

    assert simple_design[VARIABLE_TO_CHANGE] == "5mm"
    assert simple_design.evaluate_expression(simple_design[VARIABLE_PLUS_ONE]) == 0.006


def test_module_builder_success(simple_design, fake_build_module):
    """Tests that ModuleBuilder successfully loads and calls the build() function from a dynamic module."""
    builder = ModuleBuilder(
        module=fake_build_module,
        args={"design_name": "my_design", "setup_name": "Setup1"},
    )

    builder.build(
        simple_design, parameters={"name_to_value": {VARIABLE_TO_CHANGE: "4mm"}}
    )

    assert simple_design[VARIABLE_TO_CHANGE] == "4mm"
    assert simple_design.evaluate_expression(simple_design[VARIABLE_PLUS_ONE]) == 0.005


def test_module_builder_raises_on_missing_module(simple_design):
    """Tests that ModuleBuilder raises ModuleNotFoundError if the module does not exist."""
    builder = ModuleBuilder(module="non_existent_module_abcxyz", args={})

    with pytest.raises(ModuleNotFoundError):
        builder.build(simple_design)


def test_module_builder_raises_on_missing_function_name(
    simple_design, fake_build_module
):
    """Tests that ModuleBuilder raises AttributeError if the specified function doesn't exist in the module."""
    builder = ModuleBuilder(module=fake_build_module, function="stam", args={})

    with pytest.raises(AttributeError, match="Function 'stam' not found"):
        builder.build(simple_design)


def test_module_builder_propagates_build_error(simple_design, fake_build_module):
    """Tests that exceptions raised inside the user-defined build function are propagated."""

    builder = ModuleBuilder(
        module=fake_build_module, function="build_with_error", args={}
    )

    with pytest.raises(ValueError, match="Intentional error in user build"):
        builder.build(simple_design)


def test_module_builder_with_function_without_hfss_input(
    simple_design, fake_build_module
):
    """Tests that exceptions raised inside the user-defined build function are propagated."""

    builder = ModuleBuilder(
        module=fake_build_module, function="build_without_hfss", args={}
    )

    with pytest.raises(TypeError):
        builder.build(simple_design)
