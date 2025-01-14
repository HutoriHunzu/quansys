from pydantic import BaseModel, RootModel
from typing import Literal


class BaseFormatter(BaseModel):

    def format(self, setup) -> dict:
        raise NotImplementedError




class FrequencyAndQualityFactorFormatter(BaseFormatter):
    type: Literal['freq_and_q_factor']

    def format(self, setup) -> dict[int, dict[str, float]]:
        number_of_modes = setup.properties['Modes']

        return dict(map(lambda x: (x, _get_mode_to_freq_and_quality_factor(setup, x)),
                        range(1, number_of_modes + 1)))


def _get_mode_to_freq_and_quality_factor(setup, mode_number: int):
    freq_sol = setup.get_solution_data(expressions=f'Mode({mode_number})')
    q_sol = setup.get_solution_data(expressions=f'Q({mode_number})')
    return {'freq': freq_sol.data_real()[0], 'q_factor': q_sol.data_real()[0]}

class FrequencyAndQualityFactorResult(BaseModel):
    frequency: float
    quality_factor: float


class FrequencyAndQualityFactorResults(RootModel):
    root: dict[int, FrequencyAndQualityFactorResult]

    def flatten(self) -> dict:
        def _helper():
            for mode_number, freq_and_quality_factor in self.root.items():
                for k, v in dict(freq_and_quality_factor):
                    yield f'{mode_number} {k}', v

        return dict(_helper())