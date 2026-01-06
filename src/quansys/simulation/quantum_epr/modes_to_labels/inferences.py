from pydantic import BaseModel, model_validator
from typing import Literal


class InferenceBase(BaseModel):
    """Base class for all inference techniques."""

    def infer(self, **runtime_args) -> dict[int, str]:
        """Abstract method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the infer method.")


class ManualInference(InferenceBase):
    """
    Manual inference strategy to explicitly label a specific mode.

    Attributes:
        type (Literal['manual']): Discriminator field with value `'manual'`.
        mode_number (int): The eigenmode index to which the label should be assigned.
        label (str): The label to assign.

    """

    type: Literal["manual"] = "manual"
    mode_number: int
    label: str

    def infer(self, eigenmode_results: dict[int, dict[str, float]]) -> dict[int, str]:
        """
        Assigns a predefined label to a specific mode number.

        Args:
            eigenmode_results (dict[int, dict[str, float]]):
                Dictionary of available modes and their corresponding properties.

        Returns:
            dict[int, str]: A dictionary with a single key-value pair mapping the mode number to the label.

        Raises:
            ValueError: If the mode number is not present in `eigenmode_results`.
        """
        # check it is a valid number
        if eigenmode_results.get(self.mode_number) is None:
            raise ValueError(f"mode not exists in the given result {eigenmode_results}")

        return {self.mode_number: self.label}


class OrderInference(InferenceBase):
    """
    Inference strategy based on sorting modes by a specified property and assigning labels by order.

    Attributes:
        type (Literal['order']): Discriminator field with value `'order'`.
        num (int): Number of modes to assign labels to.
        min_or_max (Literal['min', 'max']): Whether to choose modes with minimum or maximum values.
        ordered_labels_by_frequency (list[str]): List of labels to assign in the determined order.
        quantity (Literal['frequency', 'quality_factor']): The property to use for sorting modes.

    """

    type: Literal["order"] = "order"
    num: int
    min_or_max: Literal["min", "max"]
    ordered_labels_by_frequency: list[str]
    quantity: Literal["frequency", "quality_factor"]

    @model_validator(mode="after")
    def validate_number_of_labels_to_num(self):
        if self.num != len(self.ordered_labels_by_frequency):
            raise ValueError(
                f"Ordered labels by frequency need to be the same length "
                f"as of number of modes, given {self.ordered_labels_by_frequency} but the "
                f"number of modes is {self.num}"
            )

        return self

    def infer(self, eigenmode_results: dict[int, dict[str, float]]) -> dict[int, str]:
        """
        Selects and labels a number of modes by sorting them based on a specified property.

        Modes are ranked based on the `quantity` field (e.g., frequency or quality factor),
        either ascending (`min`) or descending (`max`), and labeled in the order specified
        by `ordered_labels_by_frequency`.

        Args:
            eigenmode_results (dict[int, dict[str, float]]):
                Dictionary of modes and their corresponding frequency or quality factor.

        Returns:
            dict[int, str]: Mapping from selected mode numbers to labels.

        Raises:
            ValueError: If `ordered_labels_by_frequency` length does not match `num`.
        """
        # Extract the desired quantity from mode_to_freq_and_q_factor
        mode_and_quantity = [
            (k, v[self.quantity]) for k, v in eigenmode_results.items()
        ]

        # sort
        reverse = self.min_or_max == "max"
        sorted_mode_and_quantity = sorted(
            mode_and_quantity, reverse=reverse, key=lambda x: x[1]
        )[: self.num]
        modes = list(map(lambda x: x[0], sorted_mode_and_quantity))

        # modes by ordered labels
        return {
            m: self.ordered_labels_by_frequency[i] for i, m in enumerate(sorted(modes))
        }


# Example usage
if __name__ == "__main__":
    eigenmode_results = {
        1: {"frequency": 3.5, "quality_factor": 100},
        2: {"frequency": 5.1, "quality_factor": 120},
        3: {"frequency": 5.8, "quality_factor": 90},
        4: {"frequency": 6, "quality_factor": 150},
    }

    inference = OrderInference(
        type="order",
        num=2,
        min_or_max="max",
        ordered_labels_by_frequency=["A", "B"],
        quantity="quality_factor",
    )

    result = inference.infer(eigenmode_results)
    print(result)  # Example output: {2: 'A', 4: 'B'}
