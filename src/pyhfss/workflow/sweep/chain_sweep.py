from .base import SweepAbstract
from itertools import product
from typing import Iterable
from .utils import merge_dicts


class ChainSweep(SweepAbstract):

    def __init__(self, sweepers: Iterable[SweepAbstract]):
        self.sweepers = sweepers

    def generate(self):
        for elem in product(*self.sweepers):
            yield merge_dicts(*elem)

    def update(self, **kwargs):
        for sweep in self.sweepers:
            sweep.update(**kwargs)
