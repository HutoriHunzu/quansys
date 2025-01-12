from pydantic import BaseModel
from typing import Iterable
from functools import reduce

VALUE_TYPE = float | str | bool

class Value(BaseModel):
    value: VALUE_TYPE
    unit: str = ''

    def to_str(self):
        return f'{self.value}{self.unit}'

class ValuedVariable(BaseModel):
    name: str
    value: float | str | bool
    unit: str = ''

    def to_string(self):
        return f'{self.value}{self.unit}'

    def get_value(self):
        if self.unit != '':
            return self.to_string()
        return self.value

    def to_dict(self):
        return {self.name: self.get_value()}

    def as_name_value(self):
        return {self.name: Value(value=self.value,
                                 unit=self.unit)}

    @classmethod
    def iterable_to_dict(cls, values: Iterable['ValuedVariable']):
        return reduce(lambda x, y: {**x, **y.as_name_value()}, values, {})
