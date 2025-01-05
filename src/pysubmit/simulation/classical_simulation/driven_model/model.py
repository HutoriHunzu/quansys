from ansys.aedt.core import Hfss
from ansys.aedt.core.application.analysis import Setup
from typing import Literal
from pysubmit.simulation.config_handler import ConfigProject
from pydantic import BaseModel, TypeAdapter

from .formatter import SParameterFormatter

SUPPORTED_FORMATTERS = SParameterFormatter
FORMAT_ADAPTER = TypeAdapter(SUPPORTED_FORMATTERS)


class DriveModelAnalysis(BaseModel):
    type: Literal['driven_model']
    hfss: Hfss
    config_project: ConfigProject
    setup: Setup
    formatter_type: str = 's_parameter'
    formatter_args: dict | None = None

    def analyze(self):
        # Analyze
        self.setup.analyze(cores=self.config_project.cores, gpus=self.config_project.gpus)

        # Save and exit
        self.hfss.save_project()

    def format(self) -> tuple[str, dict]:
        formatter_type = {'type': self.formatter_type}
        formatter_args = {} if self.formatter_args is None else self.formatter_args
        formatter_instance = FORMAT_ADAPTER.validate_python(dict(**formatter_type, **formatter_args))
        return self.formatter_type, formatter_instance.format(self.setup)

#
# def run(hfss: Hfss, setup, config_project: ConfigProject) -> Dict[str, list[float]]:
#     # Analyze
#     setup.analyze(cores=config_project.cores, gpus=config_project.gpus)
#
#     # Save and exit
#     hfss.save_project()
#
#     # get dict of the frequency scan and the magnitude of s_11 matrix
#     return _get_reflection_s_parameter(setup)
#
#     # return hfss
#
#
# def _get_reflection_s_parameter(setup):
#     r = setup.get_solution_data(expressions='S(1,1)')
#
#     return {'freq': r.primary_sweep_values, 's_11_mag': list(r.full_matrix_mag_phase[0]['S(1,1)'].values())}
