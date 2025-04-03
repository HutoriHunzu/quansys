from typing import Literal
from pydantic import Field
import importlib

from .base import BaseBuilder, DataHandler
from ..sweep.utils import merge_dicts
from ansys.aedt.core.hfss import Hfss


class ModuleBuilder(BaseBuilder):
    """
    A builder that imports a user-specified module from the current Python environment
    and calls a designated function (default is 'build') to modify the HFSS model.

    Example YAML usage:
    ---
    builder:
      type: "module_builder"
      module: "mypackage.subfolder"
      function: "run"  # optional; defaults to "build"
      args:
        param1: "value"
        param2: [1, 2, 3]
    ---
    """
    type: Literal["module_builder"] = "module_builder"
    module: str = Field(..., description="Fully qualified Python module path, e.g. 'mypackage.subfolder'")
    function: str = Field(default="build", description="Name of the function to call within the specified module.")
    args: dict = Field(default_factory=dict, description="Arguments to pass to the build function.")

    def build(self,
              hfss: Hfss,
              data_handler: DataHandler | None = None,
              parameters: dict | None = None) -> dict:
        """
        Imports the specified module, retrieves the designated function, and calls it
        with merged arguments from 'self.args' and the optional 'parameters'.

        Args:
            hfss (Hfss):
                The active HFSS application object.
            data_handler (DataHandler | None):
                An optional object for handling simulation or design data.
            parameters (dict | None):
                Additional parameters merged with self.args before calling the function.

        Returns:
            dict: A dictionary of results or updated parameters returned by the user's function.
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
