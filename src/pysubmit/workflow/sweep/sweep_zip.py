from .base import BaseSweep
from typing import Iterable, Literal
from pydantic import model_validator
from typing_extensions import Self


# class ZipSweep(BaseSweep):
##     type: Literal['zip']
#
#     def gen(self) -> Iterable[SWEEP_OUTPUT_DATA_TYPE]:
#         iter_lst = [variable.gen() for variable in self.data]
#         return zip(*iter_lst)
#
#     def len(self) -> int:
#         return self.data[0].len()
#
#     @model_validator(mode='after')
#     def check_same_length_for_data(self) -> Self:
#         lengths_of_variables_values = set(map(lambda x: x.len(), self.data))
#         if len(lengths_of_variables_values) != 1:
#             raise ValueError(f'Cannot do a zip sweep for different length variables: {lengths_of_variables_values}')
#         return self


class ZipSweep(BaseSweep):
    type: Literal['zip'] = 'zip'

    def parse(self, lst_of_iterators):



        return zip(*lst_of_iterators)

    @model_validator(mode='after')
    def check_same_length_for_data(self) -> Self:
        lst_of_iterators = self.unpack()
        lengths_of_variables_values = set(map(lambda x: len(list(x)), lst_of_iterators))
        # there are two options:
        # there are iterators of length 1 and the rest of length N
        # all are of length N (can be 1 or something else)
        if len(lengths_of_variables_values) != 1:
            raise ValueError(f'Cannot do a zip sweep for different length variables: {lengths_of_variables_values}')
        return self
