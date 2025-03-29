from .base import BaseBuilder, DataHandler
from typing import Literal, Iterable
from pathlib import Path
import sys
import importlib
from typing_extensions import Annotated
from pydantic import BeforeValidator, AfterValidator
from ..sweep.utils import merge_dicts

from ansys.aedt.core.hfss import Hfss


def ensure_path(value: Path | str) -> Path:
    if isinstance(value, str):
        return Path(value)
    else:
        return value


def ensure_file_exists(value: Path) -> Path:
    if not value.is_file():
        raise FileNotFoundError(f"The file {str(value.resolve())} does not exist.")
    return value


PATH_TYPE = Annotated[Path,
BeforeValidator(ensure_path),
AfterValidator(ensure_file_exists)]


class ScriptBuilder(BaseBuilder):
    type: Literal['script_builder'] = 'script_builder'
    path: PATH_TYPE
    args: dict = {}
    additional_files: list[PATH_TYPE] | None = None

    def build(self, hfss: Hfss,
              data_handler: DataHandler | None = None,
              parameters: dict | None = None) -> dict:

        module = self._load_user_module()

        parameters = parameters or {}
        combined_args = merge_dicts(self.args, parameters)

        return module.build(hfss, **combined_args)

    def _load_user_module(self):
        """
        Add the directory containing the file to `sys.path` and import the file as a module.
        """
        path = self.path

        # Extract the directory and module name
        directory = str(path.parent.resolve())
        module_name = str(path.stem)

        # Temporarily add the directory to sys.path
        sys.path.insert(0, directory)
        try:
            # Import the module
            module = importlib.import_module(module_name)
        finally:
            # Remove the directory from sys.path
            sys.path.pop(0)

        return module
