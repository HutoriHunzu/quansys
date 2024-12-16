from ansys.aedt.core import Hfss
from typing import Dict
from ..config_handler import ConfigProject


def run(hfss: Hfss, config_project: ConfigProject) -> Dict[int, Dict[str, float]]:
    # Analyze
    hfss.analyze(cores=config_project.cores, gpus=config_project.gpus)

    # Save and exit
    hfss.save_project()

    # get all modes to freqs and
    return _get_all_modes_to_freq_and_quality_factor(hfss)

    # return hfss


def _get_all_modes_to_freq_and_quality_factor(hfss) -> Dict[int, Dict[str, float]]:
    post_api = hfss.post

    modes_names = post_api.available_report_quantities(quantities_category='Eigen Modes')

    number_of_modes = len(modes_names)

    return dict(map(lambda x: (x, _get_mode_to_freq_and_quality_factor(post_api, x)),
                    range(1, number_of_modes + 1)))


def _get_mode_to_freq_and_quality_factor(post_api, mode_number: int):
    freq_sol = post_api.get_solution_data(expressions=f'Mode({mode_number})')
    q_sol = post_api.get_solution_data(expressions=f'Q({mode_number})')
    return {'freq': freq_sol.data_real()[0], 'q_factor': q_sol.data_real()[0]}
