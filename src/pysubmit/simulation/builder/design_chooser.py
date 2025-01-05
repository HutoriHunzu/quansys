from .base import BaseBuilder
from typing import Literal, Iterable
from typing_extensions import Annotated
from pydantic import BeforeValidator

from .builder_interface import BuildInterface
from ansys.aedt.core.hfss import Hfss


def ensure_list(value: list[str] | str) -> list[str]:
    if not isinstance(value, list):
        value = [value]
    if len(value) < 1:
        raise ValueError('must be provided with at least one string')
    return value


NAMES_TYPE = Annotated[list[str], BeforeValidator(ensure_list)]


class DesignChooser(BaseBuilder):
    type: Literal['existing_project_builder'] = 'design_chooser'
    design_names: NAMES_TYPE
    setup_names: NAMES_TYPE

    def build(self, hfss: Hfss, data_handler) -> Iterable[BuildInterface]:
        for design_name, setup_name in zip(self.design_names, self.setup_names):
            hfss.set_active_design(design_name)
            yield BuildInterface(
                hfss=hfss,
                design_name=design_name,
                setup_name=setup_name
            )
