from pydantic import BaseModel, Field
from typing import Iterable, Literal
from abc import ABC, abstractmethod
from .utils import split_dict_by_type, merge_flat_dicts, flatten, unflatten

# from ...shared.variables_types import (Value, Values, GenericValues,
#                                        GenericValue, NamedValue, NamedValues)

# SweepInputDictValuesType = Value | Values | GenericValue | GenericValues
# SweepOutputDictValuesType = Value | GenericValue


class SweepBase(ABC, BaseModel):
    sweep_variables: dict = {}
    constants: dict = {}

    def parse(self):
        # go over the parameters and split them to iterable and not iterable
        # the non iterable part will be added as part of the constants
        # the iterable part will be returned to be used in the generate
        # for different types of sweeping mechanisms

        flat_parameters = flatten(self.sweep_variables)
        # divide it to constants and sweepable
        sweepable_parameters, constants_from_sweepable = split_dict_by_type(flat_parameters, Iterable)

        # in case of empty sweepable_parameters we still want to iterate a single time

        flat_constants = flatten(self.constants)
        flat_constants = merge_flat_dicts(flat_constants, constants_from_sweepable)

        # get all iterable with their corresponding keys
        sweepable_parameters_keys = sweepable_parameters.keys()
        sweepable_parameters_values = sweepable_parameters.values()

        return sweepable_parameters_keys, sweepable_parameters_values, flat_constants

    @abstractmethod
    def sweep(self, values: Iterable[Iterable]) -> Iterable[Iterable]:
        pass

    def generate(self) -> Iterable[dict]:
        keys, values, constants = self.parse()

        # in case there is nothing to sweep over just return the constants
        if len(keys) == 0 or len(values) == 0:
            yield unflatten(constants)
            return

        for combination in self.sweep(values):
            current = dict(zip(keys, combination))
            current = merge_dicts(current, constants)
            yield unflatten(current)

