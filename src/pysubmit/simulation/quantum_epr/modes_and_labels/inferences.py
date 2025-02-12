from pydantic import BaseModel, model_validator
from typing import Literal, List, Dict, Tuple
from pysubmit.simulation.eigenmode.results import EigenmodeResults


# from ..distributed_analysis import inverse_dict


class InferenceBase(BaseModel):
    """Base class for all inference techniques."""

    def infer(self, **runtime_args) -> Dict[int, str]:
        """Abstract method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the infer method.")


class ManualInference(InferenceBase):
    type: Literal['manual']
    mode_number: int
    label: str

    def infer(self, eigenmode_results: dict[int, dict[str, float]]) -> dict[int, str]:
        """Return a manually specified mode."""
        # check it is a valid number
        if eigenmode_results.get(self.mode_number) is None:
            raise ValueError(f'mode not exists in the given result {eigenmode_results}')

        return {self.mode_number: self.label}


class OrderInference(InferenceBase):
    type: Literal['order']
    num: int
    min_or_max: Literal['min', 'max']
    ordered_labels_by_frequency: List[str]
    quantity: Literal['frequency', 'quality_factor']

    @model_validator(mode='after')
    def validate_number_of_labels_to_num(self):
        if self.num != len(self.ordered_labels_by_frequency):
            raise ValueError(f'Ordered labels by frequency need to be the same length '
                             f'as of number of modes, given {self.ordered_labels_by_frequency} but the '
                             f'number of modes is {self.num}')

        return self

    def infer(self, eigenmode_results: dict[int, dict[str, float]]) -> dict[int, str]:
        """Perform some calculation to determine the mode and map to labels."""
        # Extract the desired quantity from mode_to_freq_and_q_factor
        mode_and_quantity = [(k, v[self.quantity]) for k, v in eigenmode_results.items()]

        # sort
        reverse = self.min_or_max == 'max'
        sorted_mode_and_quantity = sorted(mode_and_quantity, reverse=reverse, key=lambda x: x[1])[: self.num]
        modes = list(map(lambda x: x[0], sorted_mode_and_quantity))

        # modes by ordered labels
        return {m: self.ordered_labels_by_frequency[i] for i, m in enumerate(sorted(modes))}


# Example usage
if __name__ == "__main__":
    eigenmode_results = {1: {'frequency': 3.5, 'quality_factor': 100},
                         2: {'frequency': 5.1, 'quality_factor': 120},
                         3: {'frequency': 5.8, 'quality_factor': 90},
                         4: {'frequency': 6, 'quality_factor': 150}
                         }

    inference = OrderInference(
        type='order',
        num=2,
        min_or_max='max',
        ordered_labels_by_frequency=['A', 'B'],
        quantity='quality_factor'
    )

    result = inference.infer(eigenmode_results)
    print(result)  # Example output: {4: 'A', 2: 'B'}
