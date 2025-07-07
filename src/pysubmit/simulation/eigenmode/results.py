from copy import deepcopy

from pydantic import BaseModel, model_validator
from ..base import BaseSimulationOutput
from ansys.aedt.core.application.analysis import Setup
from functools import partial
from typing import Literal

from pysubmit.shared import Value
from ..base import (FlatDictType, validate_solution_type, validate_existing_solution, SimulationOutputTypesNames,
                    SimulationTypesNames)


class SingleModeResult(BaseModel):
    mode_number: int
    quality_factor: float
    frequency: Value
    label: str | None = None

    def format_mode_number(self):
        return self.label or f'Mode ({self.mode_number})'

    def change_frequency_unit(self, unit: str | None = None):
        self.frequency.change_unit(unit)

    def flatten(self) -> FlatDictType:
        return {
            f'{self.format_mode_number()} Freq. ({self.frequency.unit})': self.frequency.value,
            f'{self.format_mode_number()} Quality Factor': self.quality_factor,
        }


class EigenmodeResults(BaseSimulationOutput):
    type: Literal[SimulationOutputTypesNames.EIGENMODE_RESULT] = SimulationOutputTypesNames.EIGENMODE_RESULT
    results: dict[int, SingleModeResult]
    frequencies_unit: str = 'GHz'

    # mode_to_labels: dict[int, str] | None = None  # only used for formatting for the flat case

    def __getitem__(self, item) -> SingleModeResult:
        return self.results[item]

    #
    def generate_simple_form(self) -> dict[int, dict[str, float]]:
        return {
            elem.mode_number: {'frequency': elem.frequency.value,
                               'quality_factor': elem.quality_factor}
            for elem in self.results.values()
        }

    def change_frequencies_unit(self, unit: str):
        self.frequencies_unit = unit
        for v in self.results.values():
            v.change_frequency_unit(self.frequencies_unit)

    def flatten(self) -> FlatDictType:
        # sorting by mode number
        result = {}
        for mode_number in self.results.keys():
            current = self.results[mode_number].flatten()
            result.update(current)
        return result

    def generate_a_labeled_version(self, mode_to_labels: dict[int, str]) -> 'EigenmodeResults':
        new_results = {}
        modes = sorted(mode_to_labels.keys())
        for i, mode in enumerate(modes):
            label = mode_to_labels[mode]
            item = self.results[mode].model_copy()
            item.label = label
            item.mode_number = i
            new_results[i] = item
        return EigenmodeResults(results=new_results, frequencies_unit=self.frequencies_unit)

        # self.results = new_results


def _get_number_of_modes(setup: Setup):
    return setup.properties['Modes']


def _single_mode_result_extraction(setup: Setup, mode_number: int):
    freq_sol = setup.get_solution_data(expressions=f'Mode({mode_number})')
    q_sol = setup.get_solution_data(expressions=f'Q({mode_number})')

    return SingleModeResult(
        mode_number=mode_number,
        frequency=Value(value=freq_sol.data_real()[0], unit='Hz'),
        quality_factor=q_sol.data_real()[0]
    )


# class C
def get_eigenmode_results(setup: Setup, frequencies_unit: str = 'GHz') -> EigenmodeResults:
    # validation of setup and existing solution
    validate_solution_type(setup, setup_type='HfssEigen')
    validate_existing_solution(setup)

    # get number of modes and get all them
    num_of_modes = _get_number_of_modes(setup)
    extractor = partial(_single_mode_result_extraction, setup)
    lst_of_single_mode_results = map(extractor, range(1, num_of_modes + 1))

    # changing from a list of single mode results to a dict of mode number
    # to single mode result
    dict_of_single_mode_results = dict(map(lambda x: (x.mode_number, x), lst_of_single_mode_results))

    results = EigenmodeResults(
        results=dict_of_single_mode_results,
        frequencies_unit=frequencies_unit)

    # make same units
    results.change_frequencies_unit(frequencies_unit)

    return results
