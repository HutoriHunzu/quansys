from pydantic import BaseModel, TypeAdapter, Field
from typing import Annotated
from .inferences import ManualInference, OrderInference

SUPPORTED_INFERENCES = Annotated[ManualInference | OrderInference, Field(discriminator='type')]
"""
Union of supported inference types for mode labeling.

Includes:
- [`ManualInference`][quansys.simulation.quantum_epr.modes_to_labels.ManualInference]
- [`OrderInference`][quansys.simulation.quantum_epr.modes_to_labels.OrderInference]
"""
INFERENCE_ADAPTER = TypeAdapter(SUPPORTED_INFERENCES)


class ModesToLabels(BaseModel):
    """
    A scheme for assigning labels to eigenmodes using a list of inference rules.

    This class orchestrates the application of multiple inference strategies,
    first applying all [`ManualInference`][quansys.simulation.quantum_epr.modes_to_labels.ManualInference]
    and then [`OrderInference`][quansys.simulation.quantum_epr.modes_to_labels.OrderInference]
    in sequence to extract labels for eigenmodes.

    Attributes:
        inferences (list[SUPPORTED_INFERENCES]):
            A list of inference strategies. Each must be either
            [`ManualInference`][quansys.simulation.quantum_epr.modes_to_labels.ManualInference]
            or [`OrderInference`][quansys.simulation.quantum_epr.modes_to_labels.OrderInference].

    """
    inferences: list[SUPPORTED_INFERENCES]

    def parse(self, eigenmode_results: dict[int, dict[str, float]]) -> dict[int, str]:
        """
        Applies all configured inference rules to generate a mapping from mode numbers to labels.

        Manual inferences are executed before automatic (order-based) inferences.
        Once a mode is labeled by an inference, it is excluded from further processing by others.

        Args:
            eigenmode_results (dict[int, dict[str, float]]):
                A dictionary where each key is a mode number, and the value is a dictionary
                of mode properties such as frequency or quality factor.

        Returns:
            dict[int, str]: A mapping from mode number to assigned label.
        """

        # first execution of manual inferences
        manual_inferences = filter(lambda x: isinstance(x, ManualInference), self.inferences)
        other_inferences = filter(lambda x: not isinstance(x, ManualInference), self.inferences)

        modes_to_labels = {}

        #
        inference_execution_order = [manual_inferences, other_inferences]

        for group in inference_execution_order:
            for inference in group:

                d = inference.infer(eigenmode_results)

                new_modes = set(d.keys())
                available_modes = set(eigenmode_results.keys()) - new_modes
                eigenmode_results = {m: eigenmode_results[m] for m in available_modes}

                modes_to_labels.update(d)

        return modes_to_labels
