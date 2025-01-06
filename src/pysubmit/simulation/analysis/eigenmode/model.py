from ansys.aedt.core import Hfss
from ansys.aedt.core.application.analysis import Setup
from typing import Literal
from pysubmit.simulation.config_handler import ConfigProject
from pydantic import BaseModel, TypeAdapter

from .formatter import FrequencyAndQualityFactorFormatter

SUPPORTED_FORMATTERS = FrequencyAndQualityFactorFormatter
FORMAT_ADAPTER = TypeAdapter(SUPPORTED_FORMATTERS)


class EignModeAnalysis(BaseModel):
    type: Literal['eigenmode']
    hfss: Hfss
    config_project: ConfigProject
    setup: Setup
    formatter_type: str = 'freq_and_q_factor'
    formatter_args: dict | None = None

    def analyze(self):

        if self.config_project.min_passes:
            self.setup.props['MinimumConvergedPasses'] = self.config_project.min_passes
            self.setup.props['MinimumPasses'] = self.config_project.min_passes

        if self.config_project.max_passes:
            self.setup.props['MaximumPasses'] = self.config_project.max_passes

        # Analyze
        self.setup.analyze(cores=self.config_project.cores, gpus=self.config_project.gpus)

        # Save and exit
        self.hfss.save_project()


    def format(self) -> tuple[str, dict]:
        formatter_type = {'type': self.formatter_type}
        formatter_args = {} if self.formatter_args is None else self.formatter_args
        formatter_instance = FORMAT_ADAPTER.validate_python(dict(**formatter_type, **formatter_args))
        return self.formatter_type, formatter_instance.format(self.setup)


# def run(hfss: Hfss, setup, config_project: ConfigProject) -> Dict[int, Dict[str, float]]:
#     # make sure setup is correct
#     # setup = hfss.get_setup(config_project.setup_name)
#
#     # get all modes to freqs and
#     return _get_all_modes_to_freq_and_quality_factor(hfss)
#
#     # return hfss
#
#
# def _get_all_modes_to_freq_and_quality_factor(hfss) -> Dict[int, Dict[str, float]]:
#     post_api = hfss.post
#
#     modes_names = post_api.available_report_quantities(quantities_category='Eigen Modes')
#
#     number_of_modes = len(modes_names)
#
#     return dict(map(lambda x: (x, _get_mode_to_freq_and_quality_factor(post_api, x)),
#                     range(1, number_of_modes + 1)))
#
#
# def _get_mode_to_freq_and_quality_factor(post_api, mode_number: int):
#     freq_sol = post_api.get_solution_data(expressions=f'Mode({mode_number})')
#     q_sol = post_api.get_solution_data(expressions=f'Q({mode_number})')
#     return {'freq': freq_sol.data_real()[0], 'q_factor': q_sol.data_real()[0]}
