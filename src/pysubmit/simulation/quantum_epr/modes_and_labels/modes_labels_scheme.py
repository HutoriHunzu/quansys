from pydantic import BaseModel, TypeAdapter, Field
from typing import Annotated
from .inferences import ManualInference, OrderInference

SUPPORTED_INFERENCES = Annotated[ManualInference | OrderInference, Field(discriminator='type')]
INFERENCE_ADAPTER = TypeAdapter(SUPPORTED_INFERENCES)


class ModesAndLabels(BaseModel):
    inferences: list[SUPPORTED_INFERENCES]

    def parse(self, eigenmode_results: dict[int, dict[str, float]]) -> dict[int, str]:

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
