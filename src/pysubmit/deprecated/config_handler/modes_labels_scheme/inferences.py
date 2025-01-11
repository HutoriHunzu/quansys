from pydantic import BaseModel
from typing import Literal, List, Dict, Tuple

from ..distributed_analysis import inverse_dict


class InferenceBase(BaseModel):
    """Base class for all inference techniques."""

    def infer(self, **runtime_args) -> Dict[int, str]:
        """Abstract method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the infer method.")


class ManualInference(InferenceBase):
    type: Literal['manual']
    mode_number: int
    label: str

    def infer(self, mode_to_freq_and_q_factor: Dict[int, Tuple[float, float]]) -> Dict[int, str]:
        """Return a manually specified mode."""
        # check it is a valid number
        if mode_to_freq_and_q_factor.get(self.mode_number) is None:
            raise ValueError(f'mode not exists in the given result {mode_to_freq_and_q_factor}')

        return {self.mode_number: self.label}


class OrderInference(InferenceBase):
    type: Literal['order']
    num: int
    min_or_max: Literal['min', 'max']
    ordered_labels: List[str]
    quantity: Literal['freq', 'q_factor']

    def infer(self, mode_to_freq_and_q_factor: Dict[int, Tuple[float, float]]) -> Dict[int, str]:
        """Perform some calculation to determine the mode and map to labels."""
        # Extract the desired quantity from mode_to_freq_and_q_factor
        mode_to_quantity = dict(map(lambda x: (x[0], x[1][self.quantity]), mode_to_freq_and_q_factor.items()))
        quantity_to_mode = inverse_dict(mode_to_quantity)

        # sorting
        reverse = self.min_or_max == 'max'
        modes = list(map(lambda x: quantity_to_mode[x],
                         sorted(quantity_to_mode.keys(), reverse=reverse)[: self.num]))

        # modes by ordered labels
        return {m: self.ordered_labels[i] for i, m in enumerate(sorted(modes))}


# Example usage
if __name__ == "__main__":
    mode_to_freq_and_q_factor = {
        1: {'freq': 3.5, 'q_factor': 100},
        2: {'freq': 5.1, 'q_factor': 120},
        3: {'freq': 5.8, 'q_factor': 90},
        4: {'freq': 6.0, 'q_factor': 150}
    }

    inference = OrderInference(
        type='order',
        num=2,
        min_or_max='max',
        ordered_labels=['A', 'B'],
        quantity='freq'
    )

    result = inference.infer(mode_to_freq_and_q_factor)
    print(result)  # Example output: {4: 'A', 2: 'B'}
