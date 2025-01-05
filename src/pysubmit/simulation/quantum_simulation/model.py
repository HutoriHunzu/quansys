from ansys.aedt.core.application.analysis import Setup
from typing import Literal
from pysubmit.simulation.config_handler import ConfigProject
from pydantic import BaseModel, TypeAdapter
from ansys.aedt.core.hfss import Hfss

from ..config_handler.junction_scheme import ConfigJunction
from .structures import QuantumResult
from .distributed_analysis import DistributedAnalysis
from .epr_calculator import EprCalculator
# from .formatter import FrequencyAndQualityFactorFormatter

# SUPPORTED_FORMATTERS = FrequencyAndQualityFactorFormatter
# FORMAT_ADAPTER = TypeAdapter(SUPPORTED_FORMATTERS)


class QuantumEpr(BaseModel):
    type: Literal['quantum_epr']
    hfss: Hfss
    config_project: ConfigProject
    setup: Setup
    modes_to_labels: dict[int, str]
    junctions_infos: list[ConfigJunction]
    formatter_type: str = 'freq_and_q_factor'
    formatter_args: dict | None = None

    def analyze(self):
        dst = DistributedAnalysis(self.hfss,
                                  modes_to_labels=self.modes_to_labels,
                                  junctions_infos=self.junctions_infos)

        distributed_result = dst.main()

        calc = EprCalculator(participation_dataset=distributed_result)
        epr_result = calc.epr_numerical_diagonalizing()

        return QuantumResult(
            epr=epr_result,
            distributed=distributed_result
        )

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
