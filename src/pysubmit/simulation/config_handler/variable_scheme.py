from pydantic import BaseModel


class ValuedVariable(BaseModel):
    value: float | int
    unit: str = ''
