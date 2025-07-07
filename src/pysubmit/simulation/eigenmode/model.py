from ansys.aedt.core import Hfss
from typing import Literal
from ..base import (BaseAnalysis, SimulationTypesNames, set_design_and_get_setup,
                    update_setup_parameters, validate_solution_type)

from .results import get_eigenmode_results, EigenmodeResults


class EigenmodeAnalysis(BaseAnalysis):
    type: Literal[SimulationTypesNames.EIGENMODE] = SimulationTypesNames.EIGENMODE
    setup_name: str
    design_name: str
    cores: int = 4
    gpus: int = 0
    setup_parameters: dict = {}

    def analyze(self, hfss: Hfss, **kwargs) -> EigenmodeResults:
        if not isinstance(hfss, Hfss):
            raise ValueError('hfss given must be a Hfss instance')

        setup = set_design_and_get_setup(hfss, self.design_name, self.setup_name)

        # check for application of setup parameters
        update_setup_parameters(setup, self.setup_parameters)

        # validate solution type
        validate_solution_type(setup, setup_type='HfssEigen')

        # Analyze
        setup.analyze(cores=self.cores, gpus=self.gpus)

        # Save and exit
        hfss.save_project()

        return get_eigenmode_results(setup=setup)

    def check_requirement(self):
        pass

    def report(self):
        pass
