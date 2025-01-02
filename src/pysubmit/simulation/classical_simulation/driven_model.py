from ansys.aedt.core import Hfss
from typing import Dict
from ..config_handler import ConfigProject


def run(hfss: Hfss, setup, config_project: ConfigProject) -> Dict[str, list[float]]:

    # Analyze
    setup.analyze(cores=config_project.cores, gpus=config_project.gpus)

    # Save and exit
    hfss.save_project()

    # get dict of the frequency scan and the magnitude of s_11 matrix
    return _get_reflection_s_parameter(setup)

    # return hfss


def _get_reflection_s_parameter(setup):
    r = setup.get_solution_data(expressions='S(1,1)')

    return {'freq': r.primary_sweep_values, 's_11_mag': list(r.full_matrix_mag_phase[0]['S(1,1)'].values())}
