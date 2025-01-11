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


class SessionParameters(BaseModel):
    # path_to_save: str
    file_path: PATH_TYPE
    version: Literal['2024.2'] = '2024.2'
    non_graphical: bool = False
    new_desktop: bool = True
    close_on_exit: bool = True
