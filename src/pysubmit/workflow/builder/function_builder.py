from pydantic import Field
from .base import BaseBuilder, DataHandler
from typing import Literal, Callable, Iterable
from ..sweep.utils import merge_dicts


from ansys.aedt.core.hfss import Hfss


class FunctionBuilder(BaseBuilder):
    """
    Builder that delegates logic to a user-defined Python function.

    This builder is highly flexible and useful when programmatic or
    external control over the build process is needed.

    Attributes:
        type: Identifier for this builder type.
        function: Callable object (excluded from serialization).
        args: Static arguments passed to the function at runtime.
    """
    type: Literal['function_builder'] = 'function_builder'
    function: Callable[[Hfss, ...], dict] = Field(..., exclude=True)
    args: dict = Field(default_factory=dict)

    def build(self, hfss: Hfss,
              parameters: dict | None = None) -> dict:
        """
        Call the user-defined function with merged arguments.

        Args:
            hfss: Active HFSS session.
            parameters: Optional runtime parameters.

        Returns:
            dict: Output of the user-defined function.
        """

        parameters = parameters or {}
        combined_args = merge_dicts(self.args, parameters)

        return self.function(hfss, **combined_args)
