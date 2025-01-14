from .sweep_zip import ZipSweep
from .sweep_product import ProductSweep
from pydantic import TypeAdapter, Field
from typing_extensions import Annotated
from itertools import product, chain
from functools import reduce

SUPPORTED_SWEEPS = Annotated[ZipSweep | ProductSweep, Field(discriminator='type')]
SweepAdapter = TypeAdapter(SUPPORTED_SWEEPS)


def _combine_lst_dict(lst_of_dicts: list[dict]):
    d = {}
    for elem in lst_of_dicts:
        d.update(elem)
    return d


def chain_sweeps(lst_of_sweep: list[SUPPORTED_SWEEPS]):
    iter_lst = [sweep.gen() for sweep in lst_of_sweep]
    for elem in product(*iter_lst):
        yield _combine_lst_dict(list(elem))
