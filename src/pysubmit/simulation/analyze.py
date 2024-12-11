from ansys.aedt.core.hfss import Hfss
from src.pysubmit.simulation.quantum_simulation.epr_calculator import EprCalculator
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from .config_handler import Config

from classical_simulation import classical_run
from quantum_simulation import quantum_run
from  .hfss_common import variable_handler
from .hfss_common import project_handler



def main(config: Config, flags=None):


    # check status
    hfss = project_handler.hfss_open(config.config_project)

    # change variables accordingly
    variable_handler.set_variables(hfss, config.hfss_variables)

    # call for classical simulation
    classical_run(hfss)

    # save results
    infer_modes_to_labels =

    # call for quantum simulation
    quantum_run(hfss, config.junctions)

    # save results

    pass
