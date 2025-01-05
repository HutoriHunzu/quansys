from typing import Iterable
from pydantic import BaseModel, BeforeValidator
from abc import ABC, abstractmethod
from .builder_interface import BuildInterface

from ansys.aedt.core.hfss import Hfss


class BaseBuilder(BaseModel, ABC):

    @abstractmethod
    def build(self, hfss: Hfss, **kwargs) -> Iterable[BuildInterface]:
        pass

    # def prepare_hfss(self, hfss=None):
    #     """Prepare the hfss object for use."""
    #     if hfss:
    #         return hfss  # Use the already-opened instance
    #     else:
    #         # Open a new instance based on builder configuration
    #         return Hfss(
    #             version=self.config_builder.version,
    #             new_desktop=False,
    #             design=self.config_builder.design_name,
    #             project=str(Path(self.config_builder.path).resolve()),
    #             close_on_exit=True,
    #             remove_lock=True,
    #             non_graphical=self.config_builder.non_graphical,
    #         )
