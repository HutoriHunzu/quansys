from pathlib import Path

from pydantic import BaseModel, BeforeValidator
from pydantic_yaml import to_yaml_file, parse_yaml_file_as
from typing_extensions import Annotated, TypeAlias

from .builder import SUPPORTED_BUILDERS
from .sweep import SUPPORTED_SWEEPS
from .session_handler import PyaedtFileParameters
from .data_handler import DataHandler
from ..simulation import SUPPORTED_ANALYSIS
from pykit.aggregator import Aggregator


def ensure_path(s: str | Path) -> Path:
    """Ensure the input is converted to a Path object."""
    return Path(s) if isinstance(s, str) else s


PathType: TypeAlias = Annotated[Path, BeforeValidator(ensure_path)]

from pykit.sweeper import NormalizedSweep, EmptySweep


class WorkflowConfig(BaseModel):
    root_folder: PathType = 'results'
    pyaedt_file_parameters: PyaedtFileParameters
    simulations: dict[str, SUPPORTED_ANALYSIS]

    # builder phase
    builder: SUPPORTED_BUILDERS | None = None
    builder_sweep: NormalizedSweep = EmptySweep()
    aggregation_dict: dict[str, Aggregator] = {}

    def save_to_yaml(self, path: str | Path) -> None:
        """
        Save the workflow configuration to a YAML file.

        Args:
            path (str | Path): The file path where the YAML should be written.
        """
        to_yaml_file(path, self, map_indent=4)

    @classmethod
    def load_from_yaml(cls, path: str | Path) -> "WorkflowConfig":
        """
        Load the workflow configuration from a YAML file.

        Args:
            path (str | Path): The file path from which to load the YAML.

        Returns:
            WorkflowConfig: An instance of the workflow configuration.
        """
        return parse_yaml_file_as(cls, path)
