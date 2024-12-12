from ansys.aedt.core.hfss import Hfss

from .config_handler import Config

from .classical_simulation import classical_run
from .quantum_simulation import quantum_run
from .hfss_common import variable_handler
from .json_utils import json_write


def main(config: Config, flags=None):
    # check status
    # TODO: add context manager for hfss so it will be saved using final
    config_project = config.config_project
    with Hfss(version=config_project.version, new_desktop=False,
              design=config_project.design_name, project=config_project.path,
              close_on_exit=True, remove_lock=True, non_graphical=True) as hfss:
        
        _analysis(hfss, config)


def _analysis(hfss: Hfss, config: Config):
    # change variables accordingly
    variable_handler.set_variables(hfss, config.hfss_variables)

    # call for classical simulation
    mode_to_freq_and_q_factor = classical_run(hfss)
    json_write('classical_results.json', mode_to_freq_and_q_factor)

    # save results
    for modes_and_labels in config.modes_and_labels:
        mode_to_labels = modes_and_labels.parse(mode_to_freq_and_q_factor)

        # call for quantum simulation
        quantum_result = quantum_run(hfss, mode_to_labels, config.junctions)

        # infer name
        result_name = '_'.join(mode_to_labels.values())
        json_write(f'{result_name}.json', quantum_result)
