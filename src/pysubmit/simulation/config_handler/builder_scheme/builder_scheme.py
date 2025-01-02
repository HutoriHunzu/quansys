from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import Literal, Iterable

from ..project_scheme import ConfigProject
from ..variable_scheme import Variable, ValuedVariable, ConfigSweep

from .designs import two_mode_srf_cavity
from typing import Generator

import importlib
import sys
import os
import inspect
from pathlib import Path

SUPPORTED_BUILDERS = ()


# def validate_path(value: str | Path):
#     if isinstance(value, str):
#         return Path(value)
#     elif isinstance(value, Path):
#         return value
#     else:
#         raise ValueError(f'{value} needs to be either string or Path')


class TwoModesCavity(BaseModel):
    type: Literal['two_mode_srf_cavity']

    sweep: ConfigSweep | None

    def build(self, hfss, config_project: ConfigProject) -> Generator[dict, None, None]:
        for variables in self.prepare_variables():
            yield two_mode_srf_cavity.build(hfss,
                                            config_project,
                                            cavity_params=variables)

    def prepare_variables(self) -> Iterable[dict]:

        if self.sweep is None:
            return [{}]

        generator = self.sweep.generate_variation()
        return map(ValuedVariable.iterable_to_dict, generator)


# class ConfigBuilder(BaseModel):
#     builder: TwoModesCavity | None = None
#
#     def build(self, hfss, config_project: ConfigProject) -> Iterable[dict]:
#         if self.builder is None:
#             return [{}]
#
#         return self.builder.build(hfss, config_project)


class ConfigBuilder(BaseModel):
    build_path: str
    build_args: dict | None = None
    sweep: ConfigSweep | None = None


class Builder:

    def __init__(self, config: ConfigBuilder | None):
        self.config = config

    def load_build_and_parameters_cls(self):
        module = _load_user_module(self.config.build_path)
        return module.build, module.Parameters

    def validate(self):
        if self.config is None:
            return True
        build, parameters_class = self.load_build_and_parameters_cls()
        for parameters in self.prepare_variables():
            parameters_class(**parameters)
        return True

    def prepare_variables(self) -> Iterable[dict]:

        # base args
        if self.config.build_args is None:
            base_args = {}
        else:
            base_args = self.config.build_args

        # sweep
        sweep = self.config.sweep

        if sweep is None:
            yield base_args
            return

        generator_of_sweep_parameters = map(ValuedVariable.iterable_to_dict, sweep.generate_variation())
        for sweep_parameters in generator_of_sweep_parameters:
            parameters = dict(**base_args)
            parameters.update(sweep_parameters)
            yield parameters

    def yield_design(self, hfss, **runtime_data):
        if self.config is None:
            return [{}]

        build, parameters_class = self.load_build_and_parameters_cls()

        for parameters in self.prepare_variables():
            # validating parameters
            parameters = parameters_class(**parameters)

            yield from build(hfss, parameters)


def parse_builder(config: ConfigBuilder):
    # accessing the path

    # checking for config_args
    # and build function

    pass


def _load_user_module(file_path: str):
    """
    Add the directory containing the file to `sys.path` and import the file as a module.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    # Extract the directory and module name
    directory = str(path.parent.resolve())
    module_name = str(path.stem)

    # Temporarily add the directory to sys.path
    sys.path.insert(0, directory)
    try:
        # Import the module
        module = importlib.import_module(module_name)
    finally:
        # Remove the directory from sys.path
        sys.path.pop(0)

    return module


def validate_user_module(module):
    """
    Validate that the module contains the required `Parameters` class and `builder` function.
    """
    if not hasattr(module, "Parameters"):
        raise AttributeError("The module does not contain a `Parameters` class.")
    if not inspect.isclass(module.Parameters):
        raise TypeError("`Parameters` is not a class.")

    if not hasattr(module, "builder"):
        raise AttributeError("The module does not contain a `builder` function.")
    if not callable(module.builder):
        raise TypeError("`builder` is not a callable function.")

# def run_builder(file_path: str):
#     """
#     Load, validate, and execute the user-provided build file.
#     """
#     module = load_user_module(file_path)
#     validate_user_module(module)
#
#     # Instantiate Parameters and run builder
#     parameters = module.Parameters()  # Create an instance of Parameters
#     result = module.builder()  # Call the builder function
#     return parameters, result
