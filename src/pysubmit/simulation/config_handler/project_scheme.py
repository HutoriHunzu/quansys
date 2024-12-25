from pydantic import BaseModel, field_validator
from pathlib import Path


class ConfigProject(BaseModel):
    path: str
    design_name: str
    execution_dir: Path | None = ''
    setup_name: str = 'Setup1'
    min_passes: int | None = None
    max_passes: int | None = None
    version: str = "2024.2"
    non_graphical: bool = True
    gpus: int = 0
    cores: int = 4
    original_path: str | None = None

    @field_validator("execution_dir", mode="before")
    def convert_to_path(self, value):
        # Ensure the value is converted to a Path object
        if isinstance(value, str):
            return Path(value)
        if isinstance(value, Path):
            return value
        raise ValueError("execution_dir must be a string or Path")





