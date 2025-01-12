from .base import BaseBuilder, DataHandler
from typing import Literal
from ansys.aedt.core.hfss import Hfss

from .design_variables_handler import set_variables



class DesignVariableBuilder(BaseBuilder):
    type: Literal['design_variable_builder'] = 'design_variable_builder'
    design_name: str
    setup_name: str

    def build(self, hfss: Hfss,
              data_handler: DataHandler | None = None,
              parameters: dict = None):
        if parameters is None:
            return {}

        hfss.set_active_design(self.design_name)
        set_variables(hfss, parameters)
        return parameters
