from pydantic import BaseModel, BeforeValidator
from abc import abstractmethod, ABC
from typing import TypeVar, Iterable
from typing_extensions import Annotated



from ...variables import ValuedVariable, Variable


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


SWEEP_INPUT_DATA_TYPE = Annotated[list[Variable], BeforeValidator(ensure_list)]
SWEEP_OUTPUT_DATA_TYPE = Iterable[ValuedVariable]


class BaseSweep(BaseModel, ABC):
    data: SWEEP_INPUT_DATA_TYPE

    @abstractmethod
    def gen(self) -> Iterable[SWEEP_OUTPUT_DATA_TYPE]:
        pass

    @abstractmethod
    def len(self) -> int:
        pass














