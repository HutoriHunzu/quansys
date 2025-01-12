from pydantic import BaseModel, RootModel, BeforeValidator
from typing import Iterable, Literal, Annotated

""" 
This file contains information about different data types that might be useful in various cases:
1. using a value with unit to set variable in HFSS
2. sweep over different values to generating value and unit
"""


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


AllValueType = float | str | bool
AllValuesType = Annotated[list[AllValueType], BeforeValidator(ensure_list)]


class GenericValue(RootModel):
    root: AllValueType

    def gen(self):
        return [self.root]

    def __iter__(self):
        return iter(self.gen())

    def to_str(self):
        return f'{self.root}'


class GenericValues(RootModel):
    root: list[AllValueType]

    def gen(self) -> list[AllValueType]:
        return self.root

    def __iter__(self) -> Iterable[AllValueType]:
        return iter(self.gen())

    def __getitem__(self, item):
        return self.root[item]


class Value(BaseModel):
    value: AllValueType
    unit: str = ''

    def gen(self) -> Iterable[dict]:
        return [dict(self)]

    def to_str(self):
        return f'{self.value}{self.unit}'


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
