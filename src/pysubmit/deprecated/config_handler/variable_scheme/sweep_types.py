from pydantic import BaseModel, TypeAdapter
from typing import List, Iterable
from abc import abstractmethod
from .valued_variable import ValuedVariable, Variable
from itertools import product
from typing import Literal


class Sweep(BaseModel):

    @abstractmethod
    def gen(self) -> Iterable[Iterable[ValuedVariable]]:
        pass


class ProductSweep(Sweep):
    type: Literal['product']
    variables: List[Variable]

    def gen(self) -> Iterable[Iterable[ValuedVariable]]:
        iter_lst = [variable.gen() for variable in self.variables]
        return product(*iter_lst)


class ZipSweep(Sweep):
    type: Literal['zip']
    variables: List[Variable]

    def gen(self) -> Iterable[Iterable[ValuedVariable]]:

        # check the length of all the variables
        assert (len(set(map(lambda x: x.len(), self.variables))) == 1)

        iter_lst = [variable.gen() for variable in self.variables]
        return zip(*iter_lst)
