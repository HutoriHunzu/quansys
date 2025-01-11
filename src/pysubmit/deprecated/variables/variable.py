from pydantic import BaseModel, BeforeValidator
from typing import Iterable
from .valued_variable import ValuedVariable
from typing_extensions import Annotated


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


VALUE_TYPE = Annotated[list[float], BeforeValidator(ensure_list)]


class Variable(BaseModel):
    name: str
    values: VALUE_TYPE
    unit: str = ''

    def gen(self) -> Iterable[ValuedVariable]:
        for value in self.values:
            yield ValuedVariable(
                name=self.name,
                value=value,
                unit=self.unit
            )

    def len(self):
        return len(self.values)
