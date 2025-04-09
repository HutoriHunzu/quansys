from pydantic import BaseModel, Field, TypeAdapter, BeforeValidator
from typing_extensions import Any, Annotated, Iterable
from abc import ABC, abstractmethod
from .utils import split_dict_by_adapter, merge_by_update, flatten, unflatten
from pysubmit.shared.variables_types import SUPPORTED_COMPOUND_VALUES


SweepInputListType = list | tuple
SweepInputTypes = SUPPORTED_COMPOUND_VALUES | SweepInputListType
CompoundAdapter = TypeAdapter(SUPPORTED_COMPOUND_VALUES)
SweepInputTypesAdapter = TypeAdapter(SweepInputTypes)
IterableAdapter = TypeAdapter(SweepInputListType)


class SweepBase(ABC, BaseModel):
    parameters: dict = {}
    constants: dict = {}
    use_compound_types: bool = True

    def parse(self):
        # go over the parameters and split them to iterable and not iterable
        # the non iterable part will be added as part of the constants
        # the iterable part will be returned to be used in the generate
        # for different types of sweeping mechanisms

        adapter = CompoundAdapter if self.use_compound_types else None
        flat_parameters = flatten(self.parameters, adapter=adapter)
        # divide it to constants and sweepable

        adapter = SweepInputTypesAdapter if self.use_compound_types else IterableAdapter
        sweepable_parameters, constants_from_sweepable = split_dict_by_adapter(flat_parameters, adapter)

        # in case of empty sweepable_parameters we still want to iterate a single time

        flat_constants = flatten(self.constants)
        flat_constants = merge_by_update(flat_constants, constants_from_sweepable)

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
            current = merge_by_update(current, constants)
            yield unflatten(current)

