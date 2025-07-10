# metadata.py
from pydantic import BaseModel, BeforeValidator
from pathlib import Path
from datetime import datetime
from typing_extensions import Annotated, Self
from enum import StrEnum, auto
from .json_utils import json_read


# Custom Validators and Type Definitions
class Status(StrEnum):
    PENDING = auto()
    DONE = auto()


def ensure_path(s: str | Path) -> Path:
    return Path(s) if isinstance(s, str) else s


def ensure_datetime(s: str | datetime) -> datetime:
    return datetime.fromisoformat(s) if isinstance(s, str) else s


DatetimeType = Annotated[datetime, BeforeValidator(ensure_datetime)]
PathType = Annotated[Path, BeforeValidator(ensure_path)]


class DataDescription(BaseModel):
    """
    Represents metadata for a single simulation output.

    Attributes:
        path (Path): Relative file path to the saved data.
        start_timestamp (datetime): Time when the output was registered.
        status (Status): Status of the output (PENDING or DONE).
        saved_timestamp (datetime | None): Time when the output was saved.
    """
    path: PathType
    start_timestamp: DatetimeType
    status: Status = Status.PENDING
    saved_timestamp: DatetimeType | None = None


class Metadata(BaseModel):
    """
    Manages metadata for one iteration of simulation outputs.

    Attributes:
        iteration_number (int): The iteration number.
        base_path (Path): The directory for this iteration's metadata.
        id_to_description (dict[str, DataDescription]): Mapping from output identifier to its metadata.
    """
    iteration_number: int
    base_path: PathType
    id_to_description: dict[str, DataDescription] = {}

    def save(self) -> None:
        """
        Saves the metadata to 'metadata.json' in the base_path directory.
        """
        from .json_utils import write
        write(self.base_path / "metadata.json", self.model_dump_json(indent=4), use_unique=False)

    @classmethod
    def load(cls, path: Path) -> Self:
        """
        Loads metadata from 'metadata.json' located in the given base_path.

        Args:
            base_path (Path): Directory containing the metadata.json file.

        Returns:
            Metadata: An instance of Metadata loaded from file.
        """
        return json_read(path, cls=cls)

    def register(self, identifier: str) -> Path:
        """
        Registers a new simulation output by its identifier.

        Args:
            identifier (str): Unique identifier for the simulation output.

        Returns:
            Path: The relative file path to be used for saving the output.

        Raises:
            ValueError: If the identifier is already registered.
        """
        if identifier in self.id_to_description:
            raise ValueError(f"Identifier '{identifier}' is already registered.")
        file_path = (Path('.') / identifier).with_suffix(".json")
        self.id_to_description[identifier] = DataDescription(
            path=file_path,
            start_timestamp=datetime.now()
        )
        return file_path

    def mark_done(self, identifier: str) -> None:
        """
        Marks the specified simulation output as done.

        Args:
            identifier (str): Unique identifier for the output.

        Raises:
            ValueError: If the identifier is not registered.
        """
        if identifier not in self.id_to_description:
            raise ValueError(f"Identifier '{identifier}' is not registered.")
        self.id_to_description[identifier].status = Status.DONE
        self.id_to_description[identifier].saved_timestamp = datetime.now()

    def get_output_path(self, identifier: str) -> Path:
        """
        Returns the full path for the output file corresponding to the identifier.

        Args:
            identifier (str): Unique identifier for the output.

        Returns:
            Path: The absolute path to the output file.
        """
        if identifier not in self.id_to_description:
            raise ValueError(f"Identifier '{identifier}' is not registered.")
        return self.base_path / self.id_to_description[identifier].path
