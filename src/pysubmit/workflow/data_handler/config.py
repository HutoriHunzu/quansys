from pydantic import BaseModel
from .json_utils import unique_name_by_counter, json_write, json_read
from pathlib import Path
from typing import Iterable

from ...simulation import ANALYSIS_ADAPTER, SUPPORTED_ANALYSIS


class DataParameters(BaseModel):
    # file_path: str
    project_name: str
    root_directory: str = '.'


class DataHandler:

    def __init__(self, data_parameters: DataParameters):
        self.project_name = data_parameters.project_name
        self.root_directory = Path(data_parameters.root_directory)
        # self.project_directory = self.root_directory / f'{self.project_name}'
        self.results_directory = self.root_directory / 'results'
        self.solutions_directory = self.results_directory / 'solutions'

        self.tag = {}
        self.metadata = {}

    def clear(self):
        # remove current folder and solutions

        pass

    def prepare(self):
        # creating a subfolder in root for solutions and iterations
        self.solutions_directory.mkdir(parents=True, exist_ok=True)
        self.results_directory.mkdir(parents=True, exist_ok=True)

        # writing a project metadata json file
        json_write(self.results_directory / 'project.json',
                   {'project_name': self.project_name})

        # check if project metadata exists if its a different project?
        # if it does create one and update metadata

        # check the current location of solutions
        # if there are solution it updates the track of the
        # location and info about these solutions

        pass

    def add_solution(self, solution: dict, add_tag: bool = False):
        if add_tag:
            solution = dict(**solution, **self.tag)

        json_write(self.solutions_directory / 'sol.json', solution)

    def load_tag(self, tag: dict, title: str):
        self.tag = {title: tag}

    def _generate_all_solutions(self) -> Iterable[tuple[SUPPORTED_ANALYSIS, dict, dict]]:

        json_files = self.solutions_directory.glob('*.json')
        json_files = sorted(json_files, key=lambda x: x.lstat().st_mtime)

        for f in json_files:
            data = json_read(f)
            yield ANALYSIS_ADAPTER.validate_python(data['setup']), data['results'], data['build_parameters']

    def _filter_solutions(self, filter_func):
        pass

    def get_solutions(self,
                      solution_type: str,
                      design_name: str,
                      setup_name: str = None,
                      tag: dict = None):

        # lets break it by setup type
        solutions = filter(lambda x: x[0].type == solution_type and x[0].design_name == design_name,
                           self._generate_all_solutions())

        # filter only relevant designs
        # solutions = filter(lambda x: x[0].design_name == design_name, solutions)

        # now if tag filter by tag
        if setup_name:
            solutions = filter(lambda x: x[0].setup_name == setup_name, solutions)

        if tag:
            solutions = filter(lambda x: x[2] == tag, solutions)

        return list(solutions)

    def get_solution(self,
                     solution_type: str,
                     design_name: str,
                     setup_name: str = None,
                     tag: dict = None):

        solutions = self.get_solutions(solution_type, design_name, setup_name, tag)
        if not solutions or len(solutions) == 0:
            return None
        return solutions[-1]
