from typing import Literal
from pydantic import Field
import importlib

from .base import BaseBuilder, DataHandler
from ..sweep.utils import merge_dicts
from ansys.aedt.core.hfss import Hfss


class ModuleBuilder(BaseBuilder):
    """
    Builder that dynamically imports a module and calls a specified function.

    This allows you to build HFSS models using external, version-controlled scripts.
    Especially useful for reusable templates and team collaboration.

    Attributes:
        type: Identifier for this builder type.
        module: Python module path (e.g., 'mypkg.submodule').
        function: Name of the function in the module to call (default: 'build').
        args: Static arguments passed to the function.
    """

    type: Literal["module_builder"] = "module_builder"
    module: str = Field(..., description="Fully qualified Python module path, e.g. 'mypackage.subfolder'")
    function: str = Field(default="build", description="Name of the function to call within the specified module.")
    args: dict = Field(default_factory=dict, description="Arguments to pass to the build function.")

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
