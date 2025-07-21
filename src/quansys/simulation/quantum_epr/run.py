from ansys.aedt.core.hfss import Hfss
from typing import Dict, List

# from pysubmit.simulation.config_handler.junction_scheme import ConfigJunction
from .structures import QuantumResult, ConfigJunction
from .distributed_analysis import DistributedAnalysis
from .epr_calculator import EprCalculator


def run(
        hfss: Hfss,
        modes_to_labels: Dict[int, str],
        junctions_infos: List[ConfigJunction],
        ):


    dst = DistributedAnalysis(hfss,
                              modes_to_labels=modes_to_labels,
                              junctions_infos=junctions_infos)

    distributed_result = dst.main()

    # saving distributed analysis
    # json_write(dir_path / f'distributed{suffix}.json', distributed_result)

    calc = EprCalculator(participation_dataset=distributed_result)
    epr_result = calc.epr_numerical_diagonalizing()

    # saving epr calculation
    # json_write(dir_path / f'epr{suffix}.json', epr_result)

    return QuantumResult(
        epr=epr_result,
        distributed=distributed_result
    )
