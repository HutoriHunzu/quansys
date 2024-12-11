from pydantic import BaseModel


class ConfigJunction(BaseModel):
    name: str
    label: str
    inductance_variable_name: str
