from ansys.aedt.core.hfss import Hfss

from playground import mode_to_freq_and_q_factor
from src.pysubmit.simulation.quantum_simulation.epr_calculator import EprCalculator
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from .config_handler import Config

from classical_simulation import classical_run
from quantum_simulation import quantum_run
from .hfss_common import variable_handler, project_handler
from .json_utils import json_write
from pathlib import Path


def main(config: Config, flags=None):
    # check status
    # TODO: add context manager for hfss so it will be saved using final
    with Hfss(version=config.version,
              new_desktop=False,
              design=config.design_name,
              project=config.project_name,
              non_graphical=True) as hfss:

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
            tmp_name = result_name
            counter = 0
            while Path(f'{tmp_name}.json').is_file():
                counter += 1
                tmp_name = f'{result_name}_{counter}'
            result_name = tmp_name

            json_write(f'{result_name}.json', quantum_result)

