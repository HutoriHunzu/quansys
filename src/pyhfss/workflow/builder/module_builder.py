from typing import Literal
import importlib

from .base import BaseBuilder
from ..sweep.utils import merge_dicts
from ansys.aedt.core.hfss import Hfss


class ModuleBuilder(BaseBuilder):
    """
    Builder that dynamically imports a module and calls a specified function.

    This allows you to build HFSS models using external, version-controlled scripts.
    Especially useful for reusable templates and team collaboration.

    The imported function must have the following signature:

        def build(hfss: Hfss, **kwargs) -> dict:
            ...

    - `hfss`: The active HFSS session object.
    - `**kwargs`: Arbitrary keyword arguments, typically containing build parameters.
    - The function must return a dictionary with any results or output parameters.

    Example:
        ```python
        def build(hfss, name_to_value):
            for name, value in name_to_value.items():
                hfss[name] = value
            return {"status": "ok"}
        ```

    Attributes:
        type: Identifier for this builder type.
        module: Python module path (e.g., 'mypkg.submodule').
        function: Name of the function in the module to call (default: 'build').
        args: Static arguments passed to the function.
    """

    type: Literal["module_builder"] = "module_builder"
    module: str
    function: str = 'build'
    args: dict = {}

    def build(self,
              hfss: Hfss,
              parameters: dict | None = None) -> dict:
        """
        Import the specified module, call its build function with merged arguments.

        Args:
            hfss: Active HFSS session.
            parameters: Runtime arguments to merge with predefined `args`.

        Returns:
            dict: Output of the module's function call.

        Raises:
            ImportError: If the module or function cannot be imported.
            Exception: Any exception raised by the user-supplied function will propagate up.
        """
        # Merge any runtime parameters with the builder's predefined arguments
        parameters = parameters or {}
        combined_args = merge_dicts(self.args, parameters)

        # Dynamically import the specified module
        imported_module = importlib.import_module(self.module)

        # Retrieve the function (default is "build") from the imported module
        try:
            build_func = getattr(imported_module, self.function)
        except AttributeError:
            raise AttributeError(
                f"Function '{self.function}' not found in module '{self.module}'."
            )

        # Call the function, passing in the HFSS object plus merged arguments
        result = build_func(hfss, **combined_args)
        return result
