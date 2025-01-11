from contextlib import contextmanager
import h5py
from pydantic import BaseModel, Field
# from typing import List, Dict, Optional, Type, get_type_hints
import json
from typing import Iterator


class SolutionSchema(BaseModel):
    type: str = Field(..., description="Type of simulation (e.g., eigenmode, driven).")
    data: dict = Field(..., description="Simulation result data.")
    raw_data: dict | None = Field(None, description="Optional raw simulation data.")


class IterationSchema(BaseModel):
    metadata: dict = Field(..., description="Metadata for the iteration.")
    build_parameters: dict | None = Field(None, description="Build parameters for the iteration.")
    solutions: list[SolutionSchema] = Field(default_factory=list, description="List of solutions for the iteration.")


class ProjectSchema(BaseModel):
    metadata: dict = Field(..., description="Metadata for the project.")
    iterations: list[IterationSchema] = Field(default_factory=list, description="List of iterations for the project.")


class DatabaseSchema(BaseModel):
    projects: dict[str, ProjectSchema] = Field(default_factory=dict, description="Dictionary of projects.")


SUPPORTED_SCHEMAS = SolutionSchema | IterationSchema | ProjectSchema | DatabaseSchema

CLS_TYPE_TO_PARENT_AND_CREATION_TYPE_AND_NAME = {

    SolutionSchema: (IterationSchema, 'list', 'solutions'),
    IterationSchema: (ProjectSchema, 'list', 'iterations'),
    ProjectSchema: (DatabaseSchema, 'dict', 'projects'),
    DatabaseSchema: (None, None, None)

}


def resolve_paths(schema: SUPPORTED_SCHEMAS):
    parent, creation_type, name = CLS_TYPE_TO_PARENT_AND_CREATION_TYPE_AND_NAME[type(schema)]
    pass


class StructureHandler:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file = h5py.File(self.file_path, 'a')

    # @contextmanager
    # def open_file(self) -> Iterator[h5py.File]:

    # @contextmanager
    def get_group(self, path):
        with self.open_file() as f:
            # head group
            yield f[path]

    # @contextmanager
    def create_group(self, project_name: str):
        with self.open_file() as f:
            yield f.create_

        pass

    def append(self, path, data):
        """
        go to the path, expect this path to exist and having there a list
        append data to the list
        """
        pass

    def create(self, path, name, data):
        """
        go to the path, expect this path to exist and having there a dict
        add a name: data
        """
        pass

    def get_by_path(self, path):
        pass


if __name__ == '__main__':
    f = h5py.File("mytestfile.hdf5", "w")

    schema = DatabaseSchema.model_json_schema()
    print(json.dumps(schema, indent=2))
