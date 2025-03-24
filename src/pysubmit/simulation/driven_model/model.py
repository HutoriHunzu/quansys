from ansys.aedt.core import Hfss
from pydantic import BaseModel, TypeAdapter, Field

from ..base import (BaseAnalysis, SimulationTypesNames,
                    set_design_and_get_setup, update_setup_parameters,
                    )
from .formatter import SParameterFormatter
from typing import Literal

SUPPORTED_FORMATTERS = SParameterFormatter
FORMAT_ADAPTER = TypeAdapter(SUPPORTED_FORMATTERS)


class DriveModelAnalysis(BaseAnalysis):
    type: Literal[SimulationTypesNames.DRIVEN_MODEL] = SimulationTypesNames.DRIVEN_MODEL
    setup_name: str
    gpus: int = 0
    cores: int = 4
    setup_parameters: dict = Field(default_factory=dict)
    formatter_type: str = 's_parameter'
    formatter_args: dict | None = None

    def analyze(self, hfss: Hfss = None, **kwargs) -> dict:
        if not isinstance(hfss, Hfss):
            raise ValueError('hfss given must be a Hfss instance')

        # validate existence of design and setup name
        setup = set_design_and_get_setup(hfss, self.design_name, self.setup_name)

        # check for the application of setup parameters
        update_setup_parameters(setup, self.setup_parameters)

        # Analyze
        setup.analyze(cores=self.cores, gpus=self.gpus)

        # Save and exit
        hfss.save_project()

        # getting and returning results
        return self._get_results(hfss)

    def _get_results(self, hfss: Hfss = None) -> dict:
        formatter_type = {'type': self.formatter_type}
        formatter_args = {} if self.formatter_args is None else self.formatter_args
        formatter_instance = FORMAT_ADAPTER.validate_python(dict(**formatter_type, **formatter_args))

        setup = hfss.get_setup(self.setup_name)

        return formatter_instance.format(setup)
