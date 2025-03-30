from pydantic import BaseModel, Field, BeforeValidator, TypeAdapter
from pathlib import Path
from datetime import datetime
from typing import Any, Generator
from typing_extensions import Annotated, Self
import json
import shutil

# Import utility functions assumed to exist in your package.
from .json_utils import unique_name_by_counter, json_write, write, read, json_read

# Import the type adapter and base simulation output for conversion.
from ...simulation import ANALYSIS_ADAPTER, BaseSimulationOutput
from .utils import flat_data_from_json
import pandas as pd

from enum import StrEnum, auto


# -----------------------------------------------------------------------------
# Custom Validators and Type Definitions
# -----------------------------------------------------------------------------

class Status(StrEnum):
    PENDING = auto()
    DONE = auto()


def ensure_path(s: str | Path) -> Path:
    if isinstance(s, str):
        return Path(s)
    return s


def ensure_datetime(s: str | datetime) -> datetime:
    if isinstance(s, str):
        return datetime.fromisoformat(s)
    return s


DatetimeType = Annotated[datetime, BeforeValidator(ensure_datetime)]
PathType = Annotated[Path, BeforeValidator(ensure_path)]


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------

class DataDescription(BaseModel):
    """
    Represents a description for a data entry.

    Attributes:
        path (Path): Relative file path to the saved data.
        start_timestamp (datetime): Timestamp when the data entry was registered.
        status (Status): Current status of the data entry (e.g., PENDING, DONE).
        saved_timestamp (datetime | None): Timestamp when the data entry was saved.
    """
    path: PathType
    start_timestamp: DatetimeType
    status: Status = Status.PENDING
    saved_timestamp: DatetimeType | None = None


class Metadata(BaseModel):
    """
    Maintains metadata for a single iteration.

    Attributes:
        iteration_number (int): The iteration number.
        base_path (Path): The directory where the iteration metadata is stored.
        id_to_description (dict[str, DataDescription]): Mapping of data identifiers to their descriptions.
    """
    iteration_number: int
    base_path: PathType
    id_to_description: dict[str, DataDescription] = {}

    def flatten(self):
        return {'iteration_number': self.iteration_number}

    def __getitem__(self, item: str) -> DataDescription:
        return self.id_to_description[item]

    def save(self) -> None:
        """
        Saves the metadata to 'metadata.json' in the base_path directory.
        """
        write(self.base_path / "metadata.json", self.model_dump_json(indent=4), use_unique=False)

    def get_path_by_id(self, identifier: str) -> Path:
        rel_path = self.id_to_description[identifier].path
        return self.base_path / rel_path

    @classmethod
    def load(cls, path: Path) -> Self:
        """
        Loads metadata from 'metadata.json' located in the given base_path.

        Args:
            path (Path): Directory containing the metadata.json file.

        Returns:
            Metadata: An instance of Metadata loaded from file.
        """
        return json_read(path, cls=cls)

    def register(self, identifier: str) -> Path:
        """
        Registers a new data entry by its identifier.

        Args:
            identifier (str): Unique identifier for the data entry.

        Returns:
            Path: The unique file path for this data entry.

        Raises:
            ValueError: If the identifier is already registered.
        """
        if identifier in self.id_to_description:
            raise ValueError(f"Identifier '{identifier}' is already registered.")

        # Generate a relative file path (using identifier as filename with .json suffix)
        file_path = (Path('.') / identifier).with_suffix(".json")
        self.id_to_description[identifier] = DataDescription(
            path=file_path,
            start_timestamp=datetime.now()
        )
        return file_path

    def mark_done(self, identifier: str) -> None:
        """
        Marks the specified data entry as done, updating its status and saved timestamp.

        Args:
            identifier (str): Unique identifier for the data entry.

        Raises:
            ValueError: If the identifier is not registered.
        """
        if identifier not in self.id_to_description:
            raise ValueError(f"Identifier '{identifier}' is not registered.")
        self.id_to_description[identifier].status = Status.DONE
        self.id_to_description[identifier].saved_timestamp = datetime.now()


# -----------------------------------------------------------------------------
# DataHandler Class
# -----------------------------------------------------------------------------

class DataHandler(BaseModel):
    """
    Manages simulation results via a configurable folder hierarchy.

    Attributes:
        root_directory (Path): Base directory for all data.
        results_directory (Path): Subdirectory under root for results (default 'results').
        iterations_directory (Path): Subdirectory under results for iteration data (default 'iterations').
        aggregations_directory (Path): Subdirectory under results for aggregation results (default 'aggregations').
        last_iteration_path (Path | None): Most recently created iteration folder.
        counter (int): Internal counter for iteration numbering.
    """
    root_directory: PathType
    aggregation_config: dict[str, tuple[str, ...]] = {}
    results_directory: PathType = Field(default=Path("results"))
    iterations_directory: PathType = Field(default=Path("iterations"))
    aggregations_directory: PathType = Field(default=Path("aggregations"))
    last_iteration_path: PathType | None = None
    counter: int = -1

    def create_folders(self, overwrite: bool = False) -> None:
        """
        Creates the main folder hierarchy:
            - root_directory / results_directory
            - results_directory / iterations_directory
            - results_directory / aggregations_directory

        If overwrite is True and the results directory exists, it is removed before creating the structure.

        Args:
            overwrite (bool): Whether to delete existing folders before creation (default False).
        """
        if overwrite and self.root_directory.exists():
            shutil.rmtree(self.root_directory)
        self.root_directory.mkdir(parents=True, exist_ok=True)

        self.results_directory = self.root_directory / self.results_directory
        self.results_directory.mkdir(parents=True, exist_ok=True)

        self.iterations_directory = self.results_directory / self.iterations_directory
        self.iterations_directory.mkdir(parents=True, exist_ok=True)

        self.aggregations_directory = self.results_directory / self.aggregations_directory
        self.aggregations_directory.mkdir(parents=True, exist_ok=True)

    def create_new_iteration(self) -> Path:
        """
        Creates a new iteration folder (e.g., 'iteration_0', 'iteration_1', etc.),
        initializes an empty metadata file in that folder, and updates the last_iteration_path.

        Returns:
            Path: The path to the newly created iteration folder.
        """
        self.counter += 1
        iteration_folder = self.iterations_directory / f"iteration_{self.counter}"
        iteration_folder.mkdir(parents=True, exist_ok=False)

        # Initialize and save an empty Metadata instance.
        metadata = Metadata(iteration_number=self.counter, base_path=iteration_folder)
        metadata.save()

        self.last_iteration_path = iteration_folder
        return iteration_folder

    def register_identifier(self, identifier: str) -> Path:
        """
        Registers a new data entry for the current iteration, ensuring no collision,
        and returns the unique file path to be used for saving data.

        Args:
            identifier (str): Unique identifier for the data entry.

        Returns:
            Path: The file path where the data will be saved.

        Raises:
            ValueError: If no iteration folder exists.
        """
        if self.last_iteration_path is None:
            raise ValueError("No iteration folder exists. Call create_new_iteration first.")

        metadata = Metadata.load(self.last_iteration_path / 'metadata.json')
        file_path = metadata.register(identifier)
        metadata.save()
        return file_path

    def add_data_to_iteration(self, identifier: str, data: dict) -> None:
        """
        Saves the given JSON-serializable data into the current iteration folder,
        and updates the corresponding metadata entry.

        Args:
            identifier (str): Unique identifier for the data entry.
            data (dict): Data to be saved.

        Raises:
            ValueError: If no iteration folder exists.
            KeyError: If the identifier is not registered.
        """
        if self.last_iteration_path is None:
            raise ValueError("No iteration folder exists. Call create_new_iteration first.")

        metadata = Metadata.load(self.last_iteration_path / 'metadata.json')
        if identifier not in metadata.id_to_description:
            raise KeyError(f"Identifier '{identifier}' is not registered. Use register_identifier first.")

        # Resolve the stored relative path against the current iteration folder.
        file_path = self.last_iteration_path / metadata.id_to_description[identifier].path
        json_write(file_path, data)
        metadata.mark_done(identifier)
        metadata.save()

    def summarize_iterations(self) -> list[Metadata]:
        """
        Scans all iteration folders for metadata files and compiles a summary.

        Returns:
            dict[str, Any]: Dictionary mapping iteration folder names to their metadata.
        """
        return list(self._iter_metadata())

    # -------------------------------------------------------------------------
    # Aggregation Methods
    # -------------------------------------------------------------------------

    def _iter_metadata(self) -> Generator[Metadata, None, None]:
        """
        Private helper that searches for all 'metadata.json' files under the iterations
        directory, loads them as Metadata objects, orders them by iteration_number, and returns them.

        Returns:
            list[Metadata]: A sorted list of Metadata objects from all iteration folders.
        """
        metas = sorted(map(Metadata.load, self.iterations_directory.rglob("metadata.json")),
                       key=lambda x: x.iteration_number)
        yield from metas

    @staticmethod
    def merge_by_metadata(metadata: Metadata, id_tuple, adapter):
        # skipping metadata that doesn't have all the relevant ids
        if set(metadata.id_to_description.keys()) & set(id_tuple) != set(id_tuple):
            return None

        merged_data = {}
        for identifier in id_tuple:
            path = metadata.get_path_by_id(identifier)
            data = json_read(path)
            merged_data.update(flat_data_from_json(data, adapter=adapter))

        return merged_data

    def aggregate_and_save(self, adapter: TypeAdapter = None):
        aggregated_by_group = self.aggregate_by_config(config=self.aggregation_config, adapter=adapter)
        self.save_aggregation_to_csv(aggregated_by_group)

    def aggregate_by_config(self, config: dict[str, tuple[str, ...]] = None, adapter: Any = None) -> dict[
        str, list[dict[str, Any]]]:
        """
        Aggregates data across iterations based on the provided configuration.
        For each Metadata instance (from each iteration), for each aggregation key defined in config:
          - For each identifier in the tuple:
              * If the identifier is present, load its JSON data,
              * Convert it to a result object using the adapter,
              * Call its flatten() method,
              * Merge the flattened dictionary into an aggregated row.
        Returns a dictionary mapping each aggregation group to a list of flat aggregation rows.

        Args:
            config (dict[str, tuple[str, ...]]): Mapping of aggregation names to tuples of identifiers.
            adapter: Optional data adapter with a .validate_python method. Defaults to ANALYSIS_ADAPTER.

        Returns:
            dict[str, list[dict[str, Any]]]: Aggregated rows per aggregation group.
        """
        if adapter is None:
            adapter = ANALYSIS_ADAPTER

        # Initialize a dict to hold rows for each aggregation group.
        aggregated_by_group: dict[str, list[dict[str, Any]]] = {group: [] for group in config.keys()}

        for meta in self._iter_metadata():
            for agg_name, id_tuple in config.items():
                row = self.merge_by_metadata(meta, id_tuple, adapter)
                aggregated_by_group[agg_name].append(row)
        return aggregated_by_group

    def save_aggregation_to_csv(self, aggregated: dict[str, list[dict]]) -> None:
        """
        Stacks aggregated rows into separate Pandas DataFrames and saves each as a CSV file
        under the aggregations directory, with the filename matching the aggregation key.

        Args:
            config (dict[str, tuple[str, ...]]): Aggregation configuration mapping aggregation names to tuples of identifiers.
            adapter: Optional data adapter with a .validate_python method. Defaults to ANALYSIS_ADAPTER.
        """
        for group, rows in aggregated.items():
            df = pd.DataFrame(rows)
            csv_file = self.aggregations_directory / f"{group}.csv"
            df.to_csv(csv_file, index=False)

    def clear(self) -> None:
        """
        Clears the data handler state by removing the results directory and then recreating the folder hierarchy.
        """
        if self.results_directory.exists():
            shutil.rmtree(self.results_directory)
        self.create_folders()
