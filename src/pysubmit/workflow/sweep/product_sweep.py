from .base import SweepBase
from typing import Literal
from itertools import product
from typing import Iterable


class ProductSweep(SweepBase):
    type: Literal['product'] = 'product'

    def sweep(self, values: Iterable[Iterable]):
        return product(*values)
