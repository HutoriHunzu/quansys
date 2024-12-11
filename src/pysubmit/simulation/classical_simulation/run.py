from ansys.aedt.core import Hfss
from ..config_handler import ConfigProject, ValuedVariable


def run(hfss: Hfss):


    # Analyze
    hfss.analyze(gpus=3072, cores=8)

    # Save and exit
    hfss.save_project()

    # return hfss
