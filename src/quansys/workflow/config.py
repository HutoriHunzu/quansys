from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, BeforeValidator
from pydantic_yaml import to_yaml_file, parse_yaml_file_as
from typing_extensions import Annotated, TypeAlias

from pycaddy.sweeper import EmptySweep, DictSweep

from ..simulation import SUPPORTED_ANALYSIS

from .builder import SUPPORTED_BUILDERS
from .session_handler import PyaedtFileParameters
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
        root_folder: Root directory where simulation results will be saved. default: 'results'
        keep_hfss_solutions: If True the HFSS solution are kept (allowing for field plotting) for every
                        iteration. Should be False as keeping all solution takes a lot of memory. default: False
        pyaedt_file_parameters: Configuration for how the `.aedt` file is opened and managed during simulation.
            See [`PyaedtFileParameters`][quansys.workflow.session_handler.config.PyaedtFileParameters]
            for full control over versioning, licensing, and graphical behavior.

        simulations: Mapping of simulation names to simulation configuration objects.
            Each value must be one of the supported analysis types:

            - [`EigenmodeAnalysis`][quansys.simulation.eigenmode.model.EigenmodeAnalysis]
            - [`QuantumEPR`][quansys.simulation.quantum_epr.model.QuantumEPR]

            These are selected using a `type` field discriminator, as defined in `SUPPORTED_ANALYSIS`.

        builder: Optional object used to modify the HFSS model before simulation.

            Supported builder types:

            - [`DesignVariableBuilder`][quansys.workflow.builder.design_variable_builder.DesignVariableBuilder]
            - [`FunctionBuilder`][quansys.workflow.builder.function_builder.FunctionBuilder]
            - [`ModuleBuilder`][quansys.workflow.builder.module_builder.ModuleBuilder]

            The builder must define a `type` field used for runtime selection.

        builder_sweep: parameter sweep applied to the builder phase. each `DictSweep` instance
            allows for iteration over dict values.

            For example:

            `DictSweep(constants={'a':1},
            parameters={'b': [1,2], 'c':[3,4]},
            strategy='product')

            --> {'a': 1, 'b': 1, 'c': 3}
            --> {'a': 1, 'b': 1, 'c': 4}
            --> {'a': 1, 'b': 2, 'c': 3}
            --> {'a': 1, 'b': 2, 'c': 4}
            `

        aggregation_dict: Optional aggregation rules for result post-processing.

            Each key maps to a list of strings which should be all simulation identifiers.
            This dict is converted to `Aggregator` which than go for each key and aggregate
            its list of identifiers (e.g., flattening, validation, merging by UID).

            See `pycaddy.aggregator.Aggregator` for behavior.
    """
    root_folder: PathType = 'results'
    keep_hfss_solutions: bool = False
    pyaedt_file_parameters: PyaedtFileParameters
    simulations: dict[str, SUPPORTED_ANALYSIS]


    builder: SUPPORTED_BUILDERS | None = None
    builder_sweep: list[DictSweep] = EmptySweep()
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
