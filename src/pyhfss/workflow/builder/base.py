from pydantic import BaseModel
from abc import ABC, abstractmethod
from ..data_handler import DataHandler

from ansys.aedt.core.hfss import Hfss


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
