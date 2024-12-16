from pydantic import BaseModel


class ConfigProject(BaseModel):
    path: str
    design_name: str
    version: str = "2024.2"
    non_graphical: bool = True
    gpus: int = 0
    cores: int = 4
    original_path: str | None = None





