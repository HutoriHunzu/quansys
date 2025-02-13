from typing import Dict, Tuple, Any, List, Literal, TypeVar, Type, Callable, Iterable
from numpy.typing import NDArray
from .structures import EprDiagResult, ParticipationDataset
import numpy as np
from .serializer import dataclass_to_dict, dict_to_dataclass
from itertools import combinations
from ..base import BaseSimulationOutput, SimulationTypesNames, SimulationOutputTypesNames
from ..eigenmode.results import EigenmodeResults

from typing_extensions import Annotated
from pydantic import BeforeValidator, ConfigDict, PlainSerializer

T = TypeVar('T')


# def factory_custom_dataclass_before_validator(cls: Type[T], x: dict) -> T:
#     return dict_to_dataclass(cls, x)


def factory_custom_dataclass_before_validator(cls: Type[T]) -> Callable[[dict], T]:
    def validator(x: dict | Type[T]) -> T:
        if isinstance(x, dict):
            return dict_to_dataclass(cls, x)
        return x

    return validator


def custom_dataclass_serialization(x) -> dict:
    return dataclass_to_dict(x)


ParticipationDatasetType = Annotated[
    ParticipationDataset,
    BeforeValidator(factory_custom_dataclass_before_validator(ParticipationDataset)),
    PlainSerializer(custom_dataclass_serialization, return_type=dict),
]

EprDiagResultType = Annotated[
    EprDiagResult,
    BeforeValidator(factory_custom_dataclass_before_validator(EprDiagResult)),
    PlainSerializer(custom_dataclass_serialization, return_type=dict),
]


class QuantumResult(BaseSimulationOutput):
    type: Literal[SimulationOutputTypesNames.QUANTUM_EPR_RESULT] = SimulationOutputTypesNames.QUANTUM_EPR_RESULT
    epr: EprDiagResultType
    distributed: ParticipationDatasetType
    eigenmode_result: EigenmodeResults

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def flatten(self) -> dict:

        flat_dict = {}

        chi_flat_dict = dict(self._flatten_chi())
        frequencies_flat_dict = dict(self._flatten_frequencies_and_q_factors())

        flat_dict.update(chi_flat_dict)
        flat_dict.update(frequencies_flat_dict)
        return flat_dict





        # # Check if the chi matrix is all real
        #
        # # Flatten chi matrix into unique label pairs using combinations
        # for (i, label_1), (j, label_2) in combinations(enumerate(labels_order), 2):
        #     # For each unique pair of labels
        #     key = f"{label_1}__{label_2}"
        #
        #     # Directly use the real value from chi_matrix (symmetric, so i, j and j, i are identical)
        #     value = chi_matrix[i][j]
        #
        #     flat_dict[key] = value

        # # Add frequencies for each label
        # for i, label in enumerate(labels_order):
        #     flat_dict[f"{label}_frequency"] = frequencies[i]
        #
        # return flat_dict

    def _flatten_chi(self) -> Iterable[tuple[str, float]]:
        labels = self.distributed.labels_order
        chi_matrix = self.epr.chi

        if not np.isrealobj(chi_matrix):
            raise ValueError("The chi matrix contains complex values. Only real values are supported.")

        # Flatten chi matrix into unique label pairs using combinations
        for (i, label_1), (j, label_2) in combinations(enumerate(labels), 2):
            # For each unique pair of labels
            key = f"{label_1} - {label_2} Disp. ({self.epr.chi_unit}"

            # Directly use the real value from chi_matrix (symmetric, so i, j and j, i are identical)
            value = float(chi_matrix[i][j])

            yield key, value

        # flatten the diagonal
        for i, label in enumerate(labels):
            key = f"{label} Anharm. ({self.epr.chi_unit}"
            value = float(chi_matrix[i][i])

            yield key, value

    def _flatten_frequencies_and_q_factors(self):

        labels = self.distributed.labels_order
        frequencies = self.distributed.frequencies

        for label, frequency, single_mode_result in zip(labels, frequencies, self.eigenmode_result.results.values()):

            key = f'{label} Freq. ND ({self.epr.frequencies_unit})'
            value = float(frequency)

            yield key, value
            yield from single_mode_result.flatten().items()


