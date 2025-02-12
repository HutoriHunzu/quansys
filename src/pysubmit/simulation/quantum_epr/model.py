from typing import Literal
from ansys.aedt.core.hfss import Hfss
from typing_extensions import Annotated
from pydantic import BeforeValidator

from .distributed_analysis import DistributedAnalysis
from .epr_calculator import EprCalculator
from .modes_and_labels import ModesAndLabels
from pysubmit.simulation.base import (BaseAnalysis, SupportedAnalysisNames, validate_and_set_design)
from ..eigenmode.results import get_eigenmode_results

from .results import QuantumResult
from .structures import ConfigJunction


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


MODES_TO_LABELS_TYPE = ModesAndLabels | dict[int, str]
MODES_TO_LABELS_LST_TYPE = Annotated[list[MODES_TO_LABELS_TYPE], BeforeValidator(ensure_list)]
JUNCTION_INFO_TYPE = Annotated[list[ConfigJunction], BeforeValidator(ensure_list)]


class QuantumEpr(BaseAnalysis):
    design_name: str
    setup_name: str
    type: Literal[SupportedAnalysisNames.QUANTUM_EPR] = SupportedAnalysisNames.QUANTUM_EPR
    modes_to_labels: MODES_TO_LABELS_TYPE
    junctions_infos: JUNCTION_INFO_TYPE

    def analyze(self, hfss, **kwargs):

        if not isinstance(hfss, Hfss):
            raise ValueError('hfss given must be a Hfss instance')

        validate_and_set_design(hfss, self.design_name)

        # getting setup and getting
        setup = hfss.get_setup(self.setup_name)

        # getting eigenmode solution in simple form, meaning it is
        # of type dict[int, dict[str, float]
        # where the keys are the mode number and the values are frequency dict and quality factor dict
        eigenmode_result = get_eigenmode_results(setup)

        # convert modes to labels to dict of int to str
        # in case of ModesAndLabels object call for parse
        modes_to_labels = self.modes_to_labels

        if isinstance(modes_to_labels, ModesAndLabels):
            modes_to_labels = modes_to_labels.parse(eigenmode_result.generate_simple_form())

        epr, distributed = self._analyze(hfss, modes_to_labels)

        return QuantumResult(
            epr=epr,
            distributed=distributed,
            eigenmode_result=eigenmode_result.generate_a_labeled_version(modes_to_labels)
        )

    def _analyze(self, hfss: Hfss, modes_to_labels: dict[int, str]):
        dst = DistributedAnalysis(hfss,
                                  modes_to_labels=modes_to_labels,
                                  junctions_infos=self.junctions_infos)

        distributed_result = dst.main()

        calc = EprCalculator(participation_dataset=distributed_result)
        epr_result = calc.epr_numerical_diagonalizing()

        return epr_result, distributed_result


