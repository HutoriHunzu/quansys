from ansys.aedt.core import Hfss
from typing import Literal
from pydantic import Field
from ..base import (BaseAnalysis, SimulationTypesNames, set_design_and_get_setup,
                    update_setup_parameters, validate_solution_type)

from .results import get_eigenmode_results, EigenmodeResults


class EigenmodeAnalysis(BaseAnalysis):
    """
    Runs an Eigenmode simulation using an existing HFSS setup.

    This simulation extracts resonant frequencies and quality factors
    from the eigenmodes of a 3D electromagnetic structure in HFSS.

    Attributes:
        type: Type of simulation. Always set to 'eigenmode'.
        setup_name: Name of the HFSS setup to run.
        design_name: Name of the HFSS design to use.
        cores: Number of CPU cores to allocate (default is 4).
        gpus: Number of GPUs to allocate (default is 0).
        setup_parameters: Optional dictionary of parameters to override the setup configuration.
    """
    type: Literal[SimulationTypesNames.EIGENMODE] = SimulationTypesNames.EIGENMODE
    setup_name: str
    design_name: str
    cores: int = 4
    gpus: int = 0
    setup_parameters: dict = {}

    def analyze(self, hfss: Hfss) -> EigenmodeResults:
        """
        Execute the Eigenmode simulation and extract results.

        Args:
            hfss: An active HFSS project instance.

        Returns:
            EigenmodeResults: Object containing frequencies and Q-factors of each eigenmode.

        Raises:
            ValueError: If `hfss` is not a valid Hfss instance.
        """
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
        """Check simulation requirements. Currently, a placeholder."""
        pass

    def report(self):
        """Generate a simulation report. Currently, a placeholder."""
        pass
