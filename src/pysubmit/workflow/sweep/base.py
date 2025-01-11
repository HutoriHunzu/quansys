from pydantic import BaseModel, BeforeValidator
from abc import abstractmethod, ABC
from typing import TypeVar, Iterable
from typing_extensions import Annotated
from ...shared.variables import ValuedVariable, Variable


# from ...variables import ValuedVariable, Variable


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


SWEEP_INPUT_DATA_TYPE = Annotated[list[Variable], BeforeValidator(ensure_list)]
SWEEP_OUTPUT_DATA_TYPE = Iterable[ValuedVariable]


class BaseSweep(BaseModel, ABC):
    data: SWEEP_INPUT_DATA_TYPE
    # as_lst_of_variables: bool = True

    @abstractmethod
    def gen(self) -> Iterable[SWEEP_OUTPUT_DATA_TYPE]:
        pass

    def gen_as_dict(self) -> Iterable[dict]:
        for elem in self.gen():
            yield ValuedVariable.iterable_to_dict(elem)

    @abstractmethod
    def len(self) -> int:
        pass
