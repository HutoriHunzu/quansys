from .base import BaseSweep
from typing import Iterable, Literal
from .base import SWEEP_INPUT_DATA_TYPE, SWEEP_OUTPUT_DATA_TYPE
from itertools import product


# from ...variables import ValuedVariable, Variable


class ProductSweep(BaseSweep):
    type: Literal['product']

    def gen(self) -> Iterable[SWEEP_OUTPUT_DATA_TYPE]:
        # converting variables from input type to valued variable
        iter_lst = [variable.gen() for variable in self.data]
        return product(*iter_lst)

    def len(self):
        return len(list(self.gen()))
