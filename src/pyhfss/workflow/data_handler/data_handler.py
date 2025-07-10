from pydantic import BaseModel, BeforeValidator, computed_field, TypeAdapter
from pathlib import Path
from datetime import datetime
from typing import Any, TypeVar, Callable
from typing_extensions import Annotated, Literal
import shutil
import pandas as pd

from pyhfss.workflow.data_handler.json_utils import unique_name_by_counter
from .json_utils import json_write
from .metadata import Metadata
from .aggregator import Aggregator

# Define a generic type variable and a type alias for the saving function.
T = TypeVar("T")
SaveFunction = Callable[[Path, T], None]


def ensure_path(s: str | Path) -> Path:
    """Ensure the input is converted to a Path object."""
    return Path(s) if isinstance(s, str) else s


def ensure_datetime(s: str | datetime) -> datetime:
    """Ensure the input is converted to a datetime object."""
    return datetime.fromisoformat(s) if isinstance(s, str) else s


DatetimeType = Annotated[datetime, BeforeValidator(ensure_datetime)]
PathType = Annotated[Path, BeforeValidator(ensure_path)]


class DataHandler(BaseModel):
    """
    Manages simulation outputs via a folder hierarchy and delegates aggregation to an `Aggregator`.
    """
    # Primary configuration inputs
    root_directory: PathType = Path('.')
    results_dirname: str = "results"
    iterations_dirname: str = "iterations"
    aggregations_dirname: str = "aggregations"

    # Configuration for aggregation
    grouping_config: dict[str, list[str]] = {}

    # State tracking
    counter: int = -1
    last_iteration_path: PathType | None = None

    # Overwriting
    overwrite: bool = False
    use_unique: bool = True

    # Computed properties for derived paths
    @computed_field
    @property
    def results_directory(self) -> PathType:
        """Full path to the results' directory."""
        return self.root_directory / self.results_dirname

    @computed_field
    @property
    def iterations_directory(self) -> PathType:
        """Full path to the iterations' directory."""
        return self.results_directory / self.iterations_dirname

    @computed_field
    @property
    def aggregations_directory(self) -> PathType:
        """Full path to the aggregations' directory."""
        return self.results_directory / self.aggregations_dirname

    def create_folders(self) -> None:
        """
        Create the necessary folder hierarchy for storing results.

        If `overwrite` is True and `root_directory` already exists, it is deleted
        before creating a fresh structure.
        """
        if self.results_directory.exists():
            if self.overwrite:
                shutil.rmtree(self.results_directory, ignore_errors=True)
            elif self.use_unique:
                result_dir = unique_name_by_counter(self.results_directory)
                self.results_dirname = result_dir.stem

        # Create directory structure
        self.root_directory.mkdir(parents=True, exist_ok=True)
        self.results_directory.mkdir(parents=True, exist_ok=True)
        self.iterations_directory.mkdir(parents=True, exist_ok=True)
        self.aggregations_directory.mkdir(parents=True, exist_ok=True)

    def create_iteration(self) -> Path:
        """
        Create a new iteration folder (e.g., 'iteration_0', 'iteration_1') within
        `iterations_directory`, along with an empty `Metadata` file.

        Returns:
            Path: The path of the newly created iteration folder.
        """
        self.counter += 1
        iteration_folder = self.iterations_directory / f"iteration_{self.counter}"
        iteration_folder.mkdir(parents=True, exist_ok=False)

        # Create a new metadata file for this iteration
        metadata = Metadata(
            iteration_number=self.counter,
            base_path=iteration_folder
        )
        metadata.save()

        self.last_iteration_path = iteration_folder
        return iteration_folder

    def register_identifier(self, identifier: str) -> Path:
        """
        Register a new simulation output identifier in the current iteration's metadata,
        returning the file path that should be used for saving that data.

        Raises:
            ValueError: If no iteration folder has been created yet.

        Args:
            identifier (str): The unique identifier for a particular simulation output.

        Returns:
            Path: The path where the output data should be saved.
        """
        if self.last_iteration_path is None:
            raise ValueError("No iteration folder exists. Please call `create_iteration` first.")

        metadata_file = self.last_iteration_path / "metadata.json"
        metadata = Metadata.load(metadata_file)

        file_path = metadata.register(identifier)
        metadata.save()
        return file_path

    def add_generic_data(
            self,
            identifier: str,
            data: T,
            saving_handler: SaveFunction,
            register_if_new: bool = True
    ) -> Path:
        """
        Save simulation output data of generic type T using a user-supplied saving function,
        and mark the corresponding identifier as done in metadata.

        Parameters:
            identifier (str): The unique identifier for a simulation output.
            data (T): The simulation output data to be saved.
            saving_handler (Callable[[T, Path], None]): A function that takes the data and target file path, and performs the saving.
            register_if_new (bool): Register the data with the identifier if it is not already registered.

        Raises:
            ValueError: If no iteration folder has been created.
            KeyError: If `identifier` is not registered and `register_if_new` is False.
        """
        if self.last_iteration_path is None:
            raise ValueError("No iteration folder exists. Please call `create_iteration` first.")

        metadata_file = self.last_iteration_path / "metadata.json"
        metadata = Metadata.load(metadata_file)

        if identifier not in metadata.id_to_description:
            if register_if_new:
                metadata.register(identifier)
                metadata.save()
            else:
                raise KeyError(f"Identifier '{identifier}' not found. Call `register_identifier` first.")

        file_path = self.last_iteration_path / metadata.id_to_description[identifier].path

        # Delegate saving to the user-supplied saving function.
        saving_handler(file_path, data)

        metadata.mark_done(identifier)
        metadata.save()

        return file_path

    def add_data_to_iteration(
            self,
            identifier: str,
            data: dict[str, Any],
            register_if_new: bool = True
    ) -> Path:
        """
        Save simulation output JSON data under the current iteration and mark the corresponding
        identifier as done in metadata.

        This method now delegates the saving operation to the generic `add_generic_data` method,
        using `json_write` as the saving function.

        Parameters:
            identifier (str): The simulation output identifier.
            data (dict[str, Any]): JSON-serializable data.
            register_if_new (bool): If True, automatically register the identifier if missing.
        """
        return self.add_generic_data(identifier, data, json_write, register_if_new)

    def aggregate_and_save(self, adapter: TypeAdapter = None) -> None:
        """
        Use an `Aggregator` to merge the stored outputs according to `grouping_config`,
        and write each group's results into a CSV file in `aggregations_directory`.

        Args:
            adapter (TypeAdapter | Literal['analysis']):
                A Pydantic TypeAdapter for parsing/validating each output before flattening,
                or the string 'analysis' to use the default `ANALYSIS_ADAPTER`.
                Defaults to 'analysis'.
        """
        aggregator = Aggregator(
            grouping_config=self.grouping_config,
            scanning_dir=self.iterations_directory,
            adapter=adapter
        )

        aggregated_data = aggregator.aggregate()
        for group_name, rows in aggregated_data.items():
            df = pd.DataFrame(rows)
            out_csv = self.aggregations_directory / f"{group_name}.csv"
            df.to_csv(out_csv, index=False)

    def clear(self) -> None:
        """
        Remove the existing results directory (if any) and recreate the folder structure.
        Resets the iteration counter and clears `last_iteration_path`.
        """
        if self.results_directory.exists():
            shutil.rmtree(self.results_directory)

        self.create_folders()
        self.counter = -1
        self.last_iteration_path = None
