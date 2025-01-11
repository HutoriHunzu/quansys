from .sweep_zip import ZipSweep
from .sweep_product import ProductSweep
from pydantic import TypeAdapter

SUPPORTED_SWEEPS = (ZipSweep | ProductSweep)
SweepAdapter = TypeAdapter(SUPPORTED_SWEEPS)
