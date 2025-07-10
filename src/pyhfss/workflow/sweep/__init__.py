from .zip_sweep import ZipSweep
from .product_sweep import ProductSweep
from pydantic import TypeAdapter, Field
from typing_extensions import Annotated
from itertools import product
from .utils import merge_dicts
from .chain_sweep import ChainSweep
from .empty import EmptySweep
from .base import SweepAbstract

SUPPORTED_SWEEPS = Annotated[ZipSweep | ProductSweep, Field(discriminator='type')]
SweepAdapter = TypeAdapter(SUPPORTED_SWEEPS)


def chain_sweeps(lst_of_sweep: list[SUPPORTED_SWEEPS]):
    iter_lst = [sweep.generate() for sweep in lst_of_sweep]  # this is a list of list of dict
    for elem in product(*iter_lst):
        yield merge_dicts(*elem)
