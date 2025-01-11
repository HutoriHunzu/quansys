from pydantic import BaseModel
from typing import Literal


class BaseFormatter(BaseModel):

    def format(self, setup) -> dict:
        raise NotImplementedError


class FrequencyAndQualityFactorFormatter(BaseFormatter):
    type: Literal['freq_and_q_factor']

    def format(self, setup) -> dict[int, dict[str, float]]:
        # # post_api = hfss.post
        #
        # modes_names = post_api.available_report_quantities(quantities_category='Eigen Modes')
        # modes_names = post_api.available_report_quantities(quantities_category='Eigen Modes')
        #
        # number_of_modes = len(modes_names)

        number_of_modes = setup.properties['Modes']

        return dict(map(lambda x: (x, _get_mode_to_freq_and_quality_factor(setup, x)),
                        range(1, number_of_modes + 1)))


def _get_mode_to_freq_and_quality_factor(setup, mode_number: int):
    freq_sol = setup.get_solution_data(expressions=f'Mode({mode_number})')
    q_sol = setup.get_solution_data(expressions=f'Q({mode_number})')
    return {'freq': freq_sol.data_real()[0], 'q_factor': q_sol.data_real()[0]}
