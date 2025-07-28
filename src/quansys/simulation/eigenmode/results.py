from __future__ import annotations

from pydantic import BaseModel, Field
from ansys.aedt.core.application.analysis import Setup
from functools import partial
from typing import Literal

from ...shared import Value
from .profile import safe_extract_memory_gb
from ..base import BaseSimulationOutput
from ..base import (FlatDictType, validate_solution_type, validate_existing_solution, SimulationOutputTypesNames)


class SingleModeResult(BaseModel):
    """Result data for a single eigenmode."""

    mode_number: int = Field(..., description="The index number of the mode.")
    quality_factor: float = Field(..., description="The Q factor of the mode.")
    frequency: Value = Field(..., description="Frequency value with unit.")
    label: str | None = Field(None, description="Optional label for the mode.")

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
    """
    Result container for an Eigenmode simulation.

    Stores computed modes, each with its frequency and quality factor.
    Provides utilities to transform, flatten, and relabel the results.

    Attributes:
        type: Simulation result type identifier (always 'eigenmode_result').
        results: Mapping of mode index to a SingleModeResult instance.
        frequencies_unit: The unit in which frequencies are expressed (default: 'GHz').
        profile: Additional metadata or profile information.
    """

    type: Literal[SimulationOutputTypesNames.EIGENMODE_RESULT] = SimulationOutputTypesNames.EIGENMODE_RESULT
    results: dict[int, SingleModeResult] = Field(..., description="Mapping of mode index to its result.")
    frequencies_unit: str = Field('GHz', description="Unit used to report frequencies.")
    profile: dict = Field(default_factory=dict, description="Holds additional metadata or profile information.")

    def __getitem__(self, item) -> SingleModeResult:
        """
        Access a mode result by its index.

        Args:
            item: Mode index (int)

        Returns:
            SingleModeResult: Data for the requested mode.
        """
        return self.results[item]

    #
    def generate_simple_form(self) -> dict[int, dict[str, float]]:
        """
        Convert the result set to a simplified dict format.

        Returns:
            A dictionary mapping each mode to its frequency and quality factor.
        """
        return {
            elem.mode_number: {'frequency': elem.frequency.value,
                               'quality_factor': elem.quality_factor}
            for elem in self.results.values()
        }

    def change_frequencies_unit(self, unit: str):
        """
        Change the unit of all stored frequencies.

        Args:
            unit: New frequency unit (e.g., 'MHz', 'GHz', etc.)
        """
        self.frequencies_unit = unit
        for v in self.results.values():
            v.change_frequency_unit(self.frequencies_unit)

    def flatten(self) -> FlatDictType:
        """
        Flatten the result into a dictionary for tabular or CSV output.

        Returns:
            A flat dictionary with labeled keys and scalar values.
        """
        result = {}
        for mode_number in self.results.keys():
            current = self.results[mode_number].flatten()
            result.update(current)

        # adding profile summary if exists
        if self.profile:
            memory_gb_dict = safe_extract_memory_gb(self.profile)
            result.update(memory_gb_dict)

        return result

    def generate_a_labeled_version(self, mode_to_labels: dict[int, str]) -> EigenmodeResults:
        """
        Create a new result object with mode labels assigned.

        Args:
            mode_to_labels: Mapping of mode index to label string.

        Returns:
            EigenmodeResults: A labeled version of the results.
        """
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
