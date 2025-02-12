from pydantic import BaseModel, TypeAdapter
from typing import Dict, List, Tuple
from .inferences import ManualInference, OrderInference
from pysubmit.simulation.eigenmode.results import EigenmodeResults

SUPPORTED_INFERENCES = (ManualInference | OrderInference)
INFERENCE_ADAPTER = TypeAdapter(SUPPORTED_INFERENCES)


class Modes(BaseModel):
    inference_type: str
    args: dict

    def parse(self, mode_to_freq_and_q_factor: Dict[int, Dict[str, float]]) -> Dict[int, str]:
        inference_args = dict({'type': self.inference_type}, **self.args)
        inference_instance = INFERENCE_ADAPTER.validate_python(inference_args)
        return inference_instance.infer(mode_to_freq_and_q_factor)


class ModesAndLabels(BaseModel):
    modes: List[Modes]
    labels: List[str]

    def parse(self, eigenmode_results: dict[int, dict[str, float]]) -> Dict[int, str]:

        # first execution of manual inferences
        manual_modes = filter(lambda x: x.inference_type == 'manual', self.modes)
        other_modes = filter(lambda x: x.inference_type != 'manual', self.modes)

        modes_to_labels = {}

        #
        modes_execution_order = [manual_modes, other_modes]
        for group in modes_execution_order:
            for mode in group:
                d = mode.parse(eigenmode_results)

                new_modes = set(d.keys())
                available_modes = set(eigenmode_results.keys()) - new_modes
                eigenmode_results = {m: eigenmode_results[m] for m in available_modes}

                modes_to_labels.update(d)

        assert (len(list(modes_to_labels.keys())) == len(self.labels))

        return modes_to_labels
