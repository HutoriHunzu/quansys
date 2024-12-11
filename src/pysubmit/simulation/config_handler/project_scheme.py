from pydantic import BaseModel


class ConfigProject(BaseModel):
    path: str
    project_name: str
    design_name: str
    version: str = "2024.2"
