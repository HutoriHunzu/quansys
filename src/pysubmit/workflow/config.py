from __future__ import annotations

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
from pykit.sweeper import NormalizedSweep, EmptySweep
from .prepare import PrepareFolderConfig


def ensure_path(s: str | Path) -> Path:
    """Ensure the input is converted to a Path object."""
    return Path(s) if isinstance(s, str) else s


PathType: TypeAlias = Annotated[Path, BeforeValidator(ensure_path)]



class WorkflowConfig(BaseModel):
    """
    Top-level configuration model for a simulation workflow.

    This class defines how simulations are structured, executed, and aggregated. It is
    typically serialized/deserialized to YAML for reproducible workflows.

    Attributes:
        root_folder: Root directory where simulation results will be saved.
        pyaedt_file_parameters: Configuration for how the `.aedt` file is opened and managed during simulation.
            See [`PyaedtFileParameters`][pysubmit.workflow.session_handler.config.PyaedtFileParameters]
            for full control over versioning, licensing, and graphical behavior.

        simulations: Mapping of simulation names to simulation configuration objects.
            Each value must be one of the supported analysis types:

            - [`EigenmodeAnalysis`][pysubmit.simulation.eigenmode.model.EigenmodeAnalysis]
            - [`QuantumEpr`][pysubmit.simulation.quantum_epr.model.QuantumEpr]

            These are selected using a `type` field discriminator, as defined in `SUPPORTED_ANALYSIS`.

        builder: Optional object used to modify the HFSS model before simulation.

            Supported builder types:

            - [`DesignVariableBuilder`][pysubmit.workflow.builder.design_variable_builder.DesignVariableBuilder]
            - [`FunctionBuilder`][pysubmit.workflow.builder.function_builder.FunctionBuilder]
            - [`ModuleBuilder`][pysubmit.workflow.builder.module_builder.ModuleBuilder]

            The builder must define a `type` field used for runtime selection.
        builder_sweep: Optional parameter sweep applied to the builder phase.

            Accepts any normalized sweep configuration such as:

            - `DictSweep` (basic dictionary-based parameter combinations)
            - `ChainSweep` (product of multiple sweeps)
            - `EmptySweep` (default/no sweep)

            These are automatically normalized using `NormalizedSweep`.
        aggregation_dict: Optional aggregation rules for result post-processing.

            Each key maps to a list of strings which should be all simulation identifiers.
            This dict is converted to `Aggregator` which than go for each key and aggregate
            its list of identifiers (e.g., flattening, validation, merging by UID).

            See `pykit.aggregator.Aggregator` for behavior.
    """
    root_folder: PathType = 'results'
    pyaedt_file_parameters: PyaedtFileParameters
    simulations: dict[str, SUPPORTED_ANALYSIS]


    builder: SUPPORTED_BUILDERS | None = None
    builder_sweep: NormalizedSweep = EmptySweep()
    aggregation_dict: dict[str, list[str]] = {}
    prepare_folder: PrepareFolderConfig = PrepareFolderConfig()

    def save_to_yaml(self, path: str | Path) -> None:
        """
        Save this configuration to a YAML file.

        Args:
            path: Target file path.
        """
        to_yaml_file(path, self, map_indent=4)

    @classmethod
    def load_from_yaml(cls, path: str | Path) -> WorkflowConfig:
        """
        Load a workflow configuration from a YAML file.

        Args:
            path: Source file path.

        Returns:
            WorkflowConfig: Parsed configuration object.
        """
        return parse_yaml_file_as(cls, path)
