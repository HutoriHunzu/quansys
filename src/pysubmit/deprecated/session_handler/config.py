from pydantic import BaseModel
from pathlib import Path
from typing_extensions import Annotated, Literal
from pydantic import BeforeValidator


def ensure_path(value: Path | str) -> Path:
    if isinstance(value, str):
        return Path(value)
    else:
        return value


PATH_TYPE = Annotated[Path, BeforeValidator(ensure_path)]


