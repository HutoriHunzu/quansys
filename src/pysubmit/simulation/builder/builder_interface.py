from pydantic import BaseModel, Field
from ansys.aedt.core.hfss import Hfss


class BuildInterface(BaseModel):
    hfss: Hfss
    design_name: str
    setup_name: str
    tag: dict = Field(default_factory=dict)
