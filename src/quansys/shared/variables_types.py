from pydantic import BaseModel, RootModel, BeforeValidator, Field
from typing_extensions import Iterable, Literal, Annotated

import numpy as np
from .conversion import convert

""" 
This file contains information about different data types that might be useful in various cases:
1. using a value with unit to set variable in HFSS
2. sweep over different values to generating value and unit
"""


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


class RangeValues(BaseModel):
    type: Literal['range'] = 'range'
    start: float
    step: float
    end: float
    return_type: Literal['float', 'int'] = 'float'

    def __iter__(self):
        c = float if self.return_type == 'float' else int
        return map(lambda x: c(x), np.arange(self.start, self.end, self.step))


class LinSpaceValues(BaseModel):
    type: Literal['linspace'] = 'linspace'
    start: float
    number: int
    end: float
    return_type: Literal['float', 'int'] = 'float'

    def __iter__(self):
        c = float if self.return_type == 'float' else int
        return map(lambda x: c(x), np.linspace(self.start, self.end, self.number))


SUPPORTED_COMPOUND_VALUES = Annotated[RangeValues | LinSpaceValues, Field(discriminator='type')]

AllValueType = float | str | bool | None
AllValuesType = SUPPORTED_COMPOUND_VALUES | Annotated[list[AllValueType], BeforeValidator(ensure_list)]


class GenericValue(RootModel):
    root: AllValueType

    def gen(self):
        return iter(self)

    def __iter__(self):
        return iter([self.root])

    def to_str(self):
        return f'{self.root}'


class GenericValues(RootModel):
    root: AllValuesType

    def gen(self) -> Iterable[AllValueType]:
        return iter(self)

    def __iter__(self) -> Iterable[AllValueType]:
        return iter(self.root)

    # def __getitem__(self, item):
    #     return self.root[item]


class Value(BaseModel):
    value: float
    unit: str = ''

    def to_str(self):
        return f'{self.value}{self.unit}'

    def change_unit(self, unit: str | None):
        self.value, self.unit = convert(self.value, self.unit, target_unit=unit)


class Values(BaseModel):
    values: AllValuesType
    unit: str = ''

    def gen(self) -> Iterable[dict]:
        for v in self.values:
            yield dict(Value(value=v, unit=self.unit))


class NamedValue(BaseModel):
    name: str
    value: AllValueType
    unit: str = ''

    def gen(self) -> Iterable[dict]:
        return [dict(self)]

    def to_str(self):
        return f'{self.value}{self.unit}'


class NamedValues(BaseModel):
    name: str
    values: AllValuesType
    unit: str = ''

    def gen(self) -> Iterable[dict]:
        for v in self.values:
            yield dict(NamedValue(name=self.name, value=v, unit=self.unit))
