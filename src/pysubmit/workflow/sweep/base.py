from pydantic import BaseModel, RootModel
from typing import Iterable, Literal
from ...shared.variables_types import (Value, Values, GenericValues,
                                       GenericValue, NamedValue, NamedValues)

SweepInputDictValuesType = Value | Values | GenericValue | GenericValues
SweepOutputDictValuesType = Value | GenericValue


class SweepInputDict(RootModel):
    root: dict[str, SweepInputDictValuesType]

    def gen(self) -> Iterable[tuple[str, Iterable[SweepOutputDictValuesType]]]:
        for k, v in self.root.items():
            yield k, v.gen()

    def gen_values(self) -> Iterable[SweepOutputDictValuesType]:
        for v in self.root.values():
            yield v.gen()

    def gen_keys(self) -> Iterable[str]:
        return list(self.root.keys())


# SweepInputListValuesType = NamedValue | NamedValues
# SweepOutputListValuesType = NamedValue
#
#
# class SweepInputList(RootModel):
#     root: list[NamedValue | NamedValues]
#
#     def gen(self) -> Iterable[dict]:
#         for v in self.root:
#             yield v.gen()
#
#     def gen_values(self):
#         return self.gen()
#
#     def gen_keys(self):
#         return None


from abc import ABC, abstractmethod


class BaseSweep(BaseModel, ABC):
    data: SweepInputDict
    _keys: Iterable[str] | None = None

    def unpack(self):
        keys, list_of_iterators = self.data.gen_keys(), self.data.gen_values()
        self._keys = keys
        return list_of_iterators

    def pack(self, lst_of_values) -> dict:
        return {k: v for k, v in zip(self._keys, lst_of_values)}
        # if self._keys is None:
        #     return lst_of_values

    def gen(self) -> Iterable[dict]:
        lst_of_iterators = self.unpack()
        for result in self.parse(lst_of_iterators):
            yield self.pack(result)

    @abstractmethod
    def parse(self, lst_of_iterators: Iterable[Iterable]) \
            -> Iterable[Value | GenericValue]:
        pass

    def len(self) -> int:
        return len(list(self.gen()))





# if __name__ == '__main__':
#     # Example Usage
#     data1 = [NamedValues(name="var1", values=[1.0, 2.0], unit="m"),
#              NamedValue(name="var2", value=3, unit="cm"),
#              NamedValues(name="var3", values=[1.0, 2.0], unit="")]
#
#     data2 = {"var1": Values(values=[1.0, 2.0], unit="m"),
#              "var2": Value(value=3, unit="cm"),
#              'var3': [1.0, 2.0]}
#
#     data3 = {"var1": [1.0, 2.0], "var2": [3.0, 4.0]}
#     # invalid_data = {"var1": "not_a_list"}
#
#     # Test cases
#     for data in [data1, data2, data3]:
#         sweep = ProductSweep(data=data)
#         for elem in sweep.gen():
#             print(elem)
#         print('\n\n\n')

    # print(standardize_input(data1))  # Convert list[Variable] -> dict[str, Values]
    # print(standardize_input(data2))  # dict[str, Values] -> dict[str, Values]
    # print(standardize_input(data3))  # dict[str, list[float]] -> dict[str, Values]
    #
    # # This will raise a ValueError
    # try:
    #     print(standardize_input(invalid_data))
    # except ValueError as e:
    #     print(e)
