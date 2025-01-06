from typing import Iterable
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
# from .builder_interface import BuildInterface
from pysubmit.simulation.data_handler.data_handler import HDF5Handler
from ...variables import ValuedVariable

from ansys.aedt.core.hfss import Hfss

SUPPORTED_ANALYSIS =


# output format of builder
class BuildInterface(BaseModel):
    hfss: Hfss
    design_name: str
    setup_name: str
    analysis_type: SUPPORTED_ANALYSIS
    tag: dict = Field(default_factory=dict)

    def update_tag(self, new_tag: dict):
        self.tag = dict(**self.tag, **new_tag)


# input format of builder


class BaseBuilder(BaseModel, ABC):

    @abstractmethod
    def build(self,
              hfss: Hfss,
              data_handler: HDF5Handler | None = None,
              parameters: dict | None = None) -> Iterable[BuildInterface]:
        pass

    # def transform(self):
    #     pass
