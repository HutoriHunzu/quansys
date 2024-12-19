from pydantic import BaseModel


class ConfigJunction(BaseModel):
    name: str
    inductance_variable_name: str
