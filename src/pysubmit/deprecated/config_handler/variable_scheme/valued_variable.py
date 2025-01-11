from pydantic import BaseModel, TypeAdapter
from typing import List, Iterable
from abc import abstractmethod
from functools import reduce


# SUPPORTED_INFERENCES = (ManualInference | OrderInference)
# INFERENCE_ADAPTER = TypeAdapter(SUPPORTED_INFERENCES)


class ValuedVariable(BaseModel):
    name: str
    value: float | int
    unit: str = ''

    def to_string(self):
        return f'{self.value}{self.unit}'

    def to_dict(self):
        return {self.name: self.value}

    @classmethod
    def iterable_to_dict(cls, values: Iterable['ValuedVariable']):
        return reduce(lambda x, y: {**x, **y.to_dict()}, values, {})


class Variable(BaseModel):
    name: str
    values: float | List[float]
    unit: str = ''

    def gen(self) -> Iterable[ValuedVariable]:
        values = self.values
        if isinstance(self.values, float):
            values = [values]
        for value in values:
            yield ValuedVariable(
                name=self.name,
                value=value,
                unit=self.unit
            )

    def len(self):
        return len(list(self.gen()))
