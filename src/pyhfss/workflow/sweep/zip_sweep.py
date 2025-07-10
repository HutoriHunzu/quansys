from .base import SweepBase
from typing import Literal
from typing import Iterable

class ZipSweep(SweepBase):
    type: Literal['zip'] = 'zip'

    def sweep(self, values: Iterable[Iterable]):
        return zip(*values)