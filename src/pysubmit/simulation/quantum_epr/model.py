from typing import Literal
from ansys.aedt.core.hfss import Hfss
from typing_extensions import Annotated
from pydantic import BeforeValidator

from .distributed_analysis import DistributedAnalysis
from .epr_calculator import EprCalculator
from .modes_and_labels import ModesAndLabels
from pysubmit.simulation.base import BaseAnalysis, SupportedAnalysisNames, validate_and_set_deisgn, LIST_STR_TYPE
from .structures import ConfigJunction


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
    formatter_type: str = 'freq_and_q_factor'
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
            solution = data_handler.get_solution(solution_type=SupportedAnalysisNames.EIGENMODE,
                                                 design_name=self.design_name)

            result = solution[1]

            modes_to_labels = modes_to_labels.parse(mode_to_freq_and_q_factor=result)

        epr_result, distributed_result = self._analyze(hfss, modes_to_labels)

        return {'epr_result': epr_result,
                'distributed_result': distributed_result}

    def _analyze(self, hfss: Hfss, modes_to_labels: dict[int, str]):
        dst = DistributedAnalysis(hfss,
                                  modes_to_labels=modes_to_labels,
                                  junctions_infos=self.junctions_infos)

        distributed_result = dst.main()

        calc = EprCalculator(participation_dataset=self._distributed_result)
        epr_result = calc.epr_numerical_diagonalizing()

        return epr_result, distributed_result

    def format(self) -> dict:
        pass
        # if self._result is None:
        #     raise ValueError('Cannot call format before running analysis')
        # return self._result.to_dict()

    # def format(self) -> tuple[str, dict]:
    #     formatter_type = {'type': self.formatter_type}
    #     formatter_args = {} if self.formatter_args is None else self.formatter_args
    #     formatter_instance = FORMAT_ADAPTER.validate_python(dict(**formatter_type, **formatter_args))
    #     return self.formatter_type, formatter_instance.format(self.setup)

# def run(
#         hfss: Hfss,
#         modes_to_labels: Dict[int, str],
#         junctions_infos: List[ConfigJunction],
# ):
#     dst = DistributedAnalysis(hfss,
#                               modes_to_labels=modes_to_labels,
#                               junctions_infos=junctions_infos)
#
#     distributed_result = dst.main()
#
#     # saving distributed analysis
#     # json_write(dir_path / f'distributed{suffix}.json', distributed_result)
#
#     calc = EprCalculator(participation_dataset=distributed_result)
#     epr_result = calc.epr_numerical_diagonalizing()
#
#     # saving epr calculation
#     # json_write(dir_path / f'epr{suffix}.json', epr_result)
#
#     return QuantumResult(
#         epr=epr_result,
#         distributed=distributed_result
#     )
