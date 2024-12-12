from pydantic import BaseModel


class ConfigProject(BaseModel):
    path: str
    design_name: str
    version: str = "2024.2"
    original_path: str | None = None
