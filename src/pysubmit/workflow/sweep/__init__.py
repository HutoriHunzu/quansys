from .sweep_zip import ZipSweep
from .sweep_product import ProductSweep
from pydantic import TypeAdapter, Field
from typing_extensions import Annotated

SUPPORTED_SWEEPS = Annotated[ZipSweep | ProductSweep, Field(discriminator='type')]
SweepAdapter = TypeAdapter(SUPPORTED_SWEEPS)
