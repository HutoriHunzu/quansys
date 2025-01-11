from pydantic import BaseModel
from typing import Iterable
from functools import reduce


class ValuedVariable(BaseModel):
    name: str
    value: float
    unit: str = ''

    def to_string(self):
        return f'{self.value}{self.unit}'

    def to_dict(self):
        return {self.name: self.value}

    @classmethod
    def iterable_to_dict(cls, values: Iterable['ValuedVariable']):
        return reduce(lambda x, y: {**x, **y.to_dict()}, values, {})
