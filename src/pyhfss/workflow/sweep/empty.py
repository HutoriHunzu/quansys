from typing import Iterable

from .base import SweepAbstract


class EmptySweep(SweepAbstract):

    def generate(self) -> Iterable[dict]:
        return [{}]
