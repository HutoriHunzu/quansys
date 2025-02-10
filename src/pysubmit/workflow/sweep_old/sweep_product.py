from .base import BaseSweep
from typing import Literal
from itertools import product


class ProductSweep(BaseSweep):
    type: Literal['product'] = 'product'

    def parse(self, lst_of_iterators):
        return product(*lst_of_iterators)
