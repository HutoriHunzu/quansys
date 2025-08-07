from pydantic import Field
from .base import BaseBuilder
from typing import Literal, Callable
from pycaddy.dict_utils import merge_dicts


from ansys.aedt.core.hfss import Hfss


class FunctionBuilder(BaseBuilder):
    """
    Builder that delegates logic to a user-defined Python function.

    This builder is highly flexible and useful when programmatic or
    external control over the build process is needed.

    The user-supplied function must have the following signature:

        def my_builder_function(hfss: Hfss, **kwargs) -> dict:
            ...

    - `hfss`: The active HFSS session object.
    - `**kwargs`: Arbitrary keyword arguments, typically containing build parameters.
    - The function must return a dictionary with any results or output parameters.

    Example:
        ```python
        def builder_function(hfss, name_value_dict):
            for name, value in name_value_dict.items():
                hfss[name] = value
            return {"status": "ok"}
        ```

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
            parameters: Optional runtime parameters. These are merged with `args` and passed as keyword arguments to the function.

        Returns:
            dict: Output of the user-defined function.

        Raises:
            Exception: Any exception raised by the user-supplied function will propagate up.
        """

        parameters = parameters or {}
        combined_args = merge_dicts(self.args, parameters)

        return self.function(hfss, **combined_args)
