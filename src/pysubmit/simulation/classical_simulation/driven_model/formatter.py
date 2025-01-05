from pydantic import BaseModel
from typing import Literal


class BaseFormatter(BaseModel):

    def format(self, setup) -> dict:
        raise NotImplementedError


class SParameterFormatter(BaseFormatter):
    type: Literal['s_parameter_format']

    def format(self, setup) -> dict:
        r = setup.get_solution_data(expressions='S(1,1)')

        return {'freq': r.primary_sweep_values, 's_11_mag': list(r.full_matrix_mag_phase[0]['S(1,1)'].values())}
