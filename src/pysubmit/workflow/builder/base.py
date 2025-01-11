from typing import Iterable
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from ..data_handler.data_handler import HDF5Handler

from ansys.aedt.core.hfss import Hfss
from ...shared.variables import ValuedVariable, Variable


# output format of builder
# class BuildInterface(BaseModel):
#     hfss: Hfss
#     design_name: str
#     setup_name: str
#     tag: dict = Field(default_factory=dict)
#
#     def update_tag(self, new_tag: dict):
#         self.tag = dict(**self.tag, **new_tag)


class BaseBuilder(BaseModel, ABC):

    @abstractmethod
    def build(self, hfss: Hfss,
              parameters: dict | None = None) -> dict:
        pass

    # def build(self,
    #           hfss: Hfss,
    #           data_handler: HDF5Handler | None = None,
    #           parameters: dict | None = None) -> dict | None:
    #     pass

    # def transform(self):
    #     pass
