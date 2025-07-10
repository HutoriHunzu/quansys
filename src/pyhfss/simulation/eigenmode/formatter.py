from pydantic import BaseModel, RootModel
from typing import Literal

from ..base.base_formatters import BaseResult, BaseFormatter, TResult


# class BaseFormatter(BaseModel):
#
#     def format(self, setup) -> dict:
#         raise NotImplementedError


class FrequencyAndQualityFactorResult(BaseModel):
    frequency: float
    quality_factor: float


class FrequencyAndQualityFactorResults(BaseResult):
    root: dict[int, FrequencyAndQualityFactorResult]

    def __getitem__(self, item) -> FrequencyAndQualityFactorResult:
        return self.root[item]

    def items(self):
        return self.root.items()

    def flatten(self) -> dict:
        def _helper():
            for mode_number, freq_and_quality_factor in self.root.items():
                for k, v in freq_and_quality_factor.model_dump().items():
                    yield f'{mode_number}__{k}', v

        return dict(_helper())


class FrequencyAndQualityFactorFormatter(BaseFormatter):
    type: Literal['freq_and_q_factor']

    def format(self, setup) -> FrequencyAndQualityFactorResults:
        number_of_modes = setup.properties['Modes']

        d = dict(map(lambda x: (x, _get_mode_to_freq_and_quality_factor(setup, x)),
                     range(1, number_of_modes + 1)))

        return FrequencyAndQualityFactorResults.model_validate(d)

    def load(self, data: dict) -> FrequencyAndQualityFactorResults:
        return FrequencyAndQualityFactorResults.model_validate(data)


def _get_mode_to_freq_and_quality_factor(setup, mode_number: int):
    freq_sol = setup.get_solution_data(expressions=f'Mode({mode_number})')
    q_sol = setup.get_solution_data(expressions=f'Q({mode_number})')

    return FrequencyAndQualityFactorResult(
        frequency=freq_sol.data_real()[0],
        quality_factor=q_sol.data_real()[0]
    )
