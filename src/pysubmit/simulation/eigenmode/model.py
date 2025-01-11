from ansys.aedt.core import Hfss
from ansys.aedt.core.application.analysis import Setup
from typing import Literal
from pydantic import TypeAdapter, Field, BeforeValidator
from typing_extensions import Annotated
from ..base import (BaseAnalysis, SupportedAnalysisNames, set_design_and_get_setup,
                    update_setup_parameters, LIST_STR_TYPE)

from .formatter import FrequencyAndQualityFactorFormatter

SUPPORTED_FORMATTERS = FrequencyAndQualityFactorFormatter
FORMAT_ADAPTER = TypeAdapter(SUPPORTED_FORMATTERS)


class EignmodeAnalysis(BaseAnalysis):
    type: Literal[SupportedAnalysisNames.EIGENMODE] = SupportedAnalysisNames.EIGENMODE
    setup_name: str
    cores: int = 4
    gpus: int = 0
    setup_parameters: dict = Field(default_factory=dict)
    formatter_type: str = 'freq_and_q_factor'
    formatter_args: dict | None = None

    def analyze(self, hfss: Hfss = None, **kwargs) -> dict:
        if not isinstance(hfss, Hfss):
            raise ValueError('hfss given must be a Hfss instance')

        # if self.config_project.min_passes:
        #     self.setup.props['MinimumConvergedPasses'] = self.config_project.min_passes
        #     self.setup.props['MinimumPasses'] = self.config_project.min_passes
        #
        # if self.config_project.max_passes:
        #     self.setup.props['MaximumPasses'] = self.config_project.max_passes
        setup = set_design_and_get_setup(hfss, self.design_name, self.setup_name)

        # check for application of setup parameters
        update_setup_parameters(setup, self.setup_parameters)

        # Analyze
        setup.analyze(cores=self.cores, gpus=self.gpus)

        # Save and exit
        hfss.save_project()

        return self._get_results(hfss)

    def _get_results(self, hfss: Hfss = None) -> dict:
        formatter_type = {'type': self.formatter_type}
        formatter_args = {} if self.formatter_args is None else self.formatter_args
        formatter_instance = FORMAT_ADAPTER.validate_python(dict(**formatter_type, **formatter_args))

        # getting setup
        setup = hfss.get_setup(self.setup_name)

        return formatter_instance.format(setup)

    def extract_parameters(self) -> dict:
        return dict(self)

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
