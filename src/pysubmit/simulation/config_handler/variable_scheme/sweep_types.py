from pydantic import BaseModel, TypeAdapter
from typing import List, Iterable
from abc import abstractmethod
from .valued_variable import ValuedVariable, Variable
from itertools import product


class Sweep(BaseModel):

    @abstractmethod
    def gen(self) -> Iterable[Iterable[ValuedVariable]]:
        pass


class ProductSweep(Sweep):
    type: str = 'product'
    args: List[Variable]

    def gen(self) -> Iterable[Iterable[ValuedVariable]]:
        variables = self.args
        iter_lst = [variable.gen() for variable in variables]
        return product(*iter_lst)


class ZipSweep(Sweep):
    type: str = 'zip'
    args: List[Variable]

    def gen(self) -> Iterable[Iterable[ValuedVariable]]:
        variables = self.args
        # check the length of all the variables
        assert (len(set(map(lambda x: x.len(), variables))) == 1)

        iter_lst = [variable.gen() for variable in variables]
        return zip(*iter_lst)
