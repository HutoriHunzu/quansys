from .base import BaseBuilder, DataHandler
from typing import Literal
from ansys.aedt.core.hfss import Hfss

from .design_variables_handler import set_variables



class DesignVariableBuilder(BaseBuilder):
    """
    Builder for setting design variables in an HFSS model.

    This builder sets project-level design parameters before simulation.
    It’s useful for parametrizing a model and enabling sweeps.

    Attributes:
        type: Identifier for this builder type.
        design_name: Name of the HFSS design to activate.
    """

    type: Literal['design_variable_builder'] = 'design_variable_builder'
    design_name: str

    def build(self, hfss: Hfss,
              parameters: dict = None) -> dict:

        """
        Apply design variables to the HFSS project.

        Args:
            hfss: Active HFSS session.
            parameters: Dictionary of design variables and their values.

        Returns:
            dict: The same dictionary, confirming the values set in the design.
        """

        if parameters is None:
            return {}

        hfss.set_active_design(self.design_name)
        set_variables(hfss, parameters)
        return parameters
