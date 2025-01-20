from typing import Literal
from ansys.aedt.core.hfss import Hfss
from typing_extensions import Annotated
from pydantic import BeforeValidator

from .distributed_analysis import DistributedAnalysis
from .epr_calculator import EprCalculator
from .modes_and_labels import ModesAndLabels
from pysubmit.simulation.base import BaseAnalysis, SupportedAnalysisNames, validate_and_set_deisgn, LIST_STR_TYPE
from .structures import ConfigJunction, QuantumResult


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


MODES_TO_LABELS_TYPE = ModesAndLabels | dict[int, str]
MODES_TO_LABELS_LST_TYPE = Annotated[list[MODES_TO_LABELS_TYPE], BeforeValidator(ensure_list)]
JUNCTION_INFO_TYPE = Annotated[list[ConfigJunction], BeforeValidator(ensure_list)]


class QuantumEpr(BaseAnalysis):
    type: Literal[SupportedAnalysisNames.QUANTUM_EPR] = SupportedAnalysisNames.QUANTUM_EPR
    modes_to_labels: MODES_TO_LABELS_TYPE
    junctions_infos: JUNCTION_INFO_TYPE
    formatter_type: str | None = 'dispersive'
    formatter_args: dict | None = None

    # keeps the result until calling for format
    # result: dict = Field(init=False, default_factory=list)

    # _distributed_result: ParticipationDataset = None

    def analyze(self, hfss, data_handler=None, **kwargs):

        # hfss = kwargs.get('hfss')
        # data_handler = kwargs.get('data_handler')

        if not isinstance(hfss, Hfss):
            raise ValueError('hfss given must be a Hfss instance')

        validate_and_set_deisgn(hfss, self.design_name)

        # convert modes to labels to dict of int to str
        # in case of ModesAndLabels object call for parse
        modes_to_labels = self.modes_to_labels
        if isinstance(modes_to_labels, ModesAndLabels):
            # getting the latest solution of eigenmode to be used for the modes and labels
            solution = data_handler.get_solution(setup_discriminator=SupportedAnalysisNames.EIGENMODE)

            result = solution.result

            modes_to_labels = modes_to_labels.parse(mode_to_freq_and_q_factor=result)

        return self._analyze(hfss, modes_to_labels)

    def _analyze(self, hfss: Hfss, modes_to_labels: dict[int, str]):
        dst = DistributedAnalysis(hfss,
                                  modes_to_labels=modes_to_labels,
                                  junctions_infos=self.junctions_infos)

        distributed_result = dst.main()

        calc = EprCalculator(participation_dataset=distributed_result)
        epr_result = calc.epr_numerical_diagonalizing()

        return QuantumResult(
            epr=epr_result,
            distributed=distributed_result
        )

        # return epr_result, distributed_result

    @staticmethod
    def convert_result_to_dict(result: QuantumResult) -> dict:
        return result.to_dict()

    # @staticmethod
    def load_result_by_dict(self, data: dict) -> QuantumResult:
        return QuantumResult.from_dict(data)

    def format(self) -> dict:
        # format the result to flatten
        pass
