from ansys.aedt.core import Hfss
from ansys.aedt.core.application.analysis import SetupHFSS
from typing import Literal
from pydantic import TypeAdapter, Field, BeforeValidator
from typing_extensions import Annotated
from ..base import (BaseAnalysis, SimulationTypesNames, set_design_and_get_setup,
                    update_setup_parameters, validate_solution_type)

from ..shared.solution_handler import get_solved_solutions
from .results import get_eigenmode_results


# from .formatter import FrequencyAndQualityFactorFormatter

# SUPPORTED_FORMATTERS = FrequencyAndQualityFactorFormatter
# FORMAT_ADAPTER = TypeAdapter(SUPPORTED_FORMATTERS)


class EignmodeAnalysis(BaseAnalysis):
    type: Literal[SimulationTypesNames.EIGENMODE] = SimulationTypesNames.EIGENMODE
    setup_name: str
    design_name: str
    cores: int = 4
    gpus: int = 0
    setup_parameters: dict = {}

    # formatter_type: str = 'freq_and_q_factor'
    # formatter_args: dict | None = None

    def analyze(self, hfss: Hfss = None, **kwargs):
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

        return get_eigenmode_results(setup)

    def check_requirement(self):
        pass

    def report(self):
        pass

        # hfss['chip_house_length'] = '22.2mm'

        # setup.analyze(cores=self.cores, gpus=self.gpus)

        # Save and exit
        # hfss.save_project()

        # get_solved_solutions(hfss)

    # # def _get_formatter(self):
    # #     formatter_type = {'type': self.formatter_type}
    # #     formatter_args = {} if self.formatter_args is None else self.formatter_args
    # #     return FORMAT_ADAPTER.validate_python(dict(**formatter_type, **formatter_args))
    #
    # @staticmethod
    # def convert_result_to_dict(result) -> dict:
    #     return result.model_dump()
    #
    # def load_result_by_dict(self, data: dict):
    #     formatter = self._get_formatter()
    #     return formatter.load(data)
    #
    # def _get_results(self, hfss: Hfss = None):
    #     formatter = self._get_formatter()
    #
    #     # getting setup
    #     setup = hfss.get_setup(self.setup_name)
    #
    #     return formatter.format(setup)
    #
    # def extract_parameters(self) -> dict:
    #     return self.model_dump()
