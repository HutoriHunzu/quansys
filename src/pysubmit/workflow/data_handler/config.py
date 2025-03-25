from pydantic import BaseModel, Field, validate_call, BeforeValidator
from .json_utils import unique_name_by_counter, read, write, json_write
from pathlib import Path
from typing import Iterable, Type

from ...simulation import ANALYSIS_ADAPTER, SUPPORTED_ANALYSIS, SimulationTypesNames, BaseSimulationOutput
from typing_extensions import Annotated
from itertools import islice, groupby
from datetime import datetime

from pandas import DataFrame


def convert_none_to_current_dir(value):
    if value is None:
        return '.'
    return value


POSITIVE_INTEGER = Annotated[int, Field(gt=0)]
ROOT_DIRECTORY = Annotated[str, BeforeValidator(convert_none_to_current_dir)]


class DataParameters(BaseModel):
    # file_path: str
    project_name: str
    root_directory: ROOT_DIRECTORY = '.'


class Metadata(BaseModel):
    date: datetime


class Solution(BaseModel):
    result: dict
    setup: SUPPORTED_ANALYSIS
    build_parameters: dict
    metadata: Metadata

    def flatten(self):
        result_as_obj = self.setup.load_result_by_dict(self.result)
        flatten_result = result_as_obj.flatten()
        date = {'time': self.metadata.date.isoformat()}
        d = {}
        for attr in (date, self.build_parameters, flatten_result):
            d.update(attr)
        return d

    # def discriminate_by_setup(self, value: SupportedAnalysisNames | None) -> bool:
    #     if value is None:
    #         return True
    #     return self.setup.type == value
    #
    # def discriminate_by_build_parameters(self, value: dict | None) -> bool:
    #     if value is None:
    #         return True
    #     return self.build_parameters == value

    def get_discrimination_value(self) -> tuple[SimulationTypesNames, dict]:
        return self.setup.type, self.build_parameters

    def discriminate(self,
                     setup_name: SimulationTypesNames | None = None,
                     build_parameters: dict | None = None):
        user_args = setup_name, build_parameters
        instance_args = self.get_discrimination_value()

        return all(
            a is None or a == b
            for a, b in zip(user_args, instance_args)
        )


class DataHandler:

    def __init__(self, data_parameters: DataParameters):
        self.project_name = data_parameters.project_name
        self.root_directory = Path(data_parameters.root_directory)
        # self.project_directory = self.root_directory / f'{self.project_name}'
        self.results_directory = self.root_directory / 'results'
        self.solutions_directory = self.results_directory / 'solutions'
        self.aggregate_directory = self.results_directory / 'aggregate'

        self.last_iteration_path: Path = None

        self.tag = {}
        self.metadata = {}

    def clear(self):
        # remove current folder and solutions

        pass

    def create_iteration(self) -> Path:

        path = self.results_directory / 'iteration'
        path = unique_name_by_counter(path)
        path.mkdir()
        self.last_iteration_path = path
        return path

    def add_data_to_iteration(self, title_name: str, data: dict):

        path = self.last_iteration_path / f'{title_name}.json'
        path = unique_name_by_counter(path)

        json_write(path, data)

    def prepare(self):
        # creating a subfolder in root for solutions and iterations
        self.solutions_directory.mkdir(parents=True, exist_ok=True)
        self.results_directory.mkdir(parents=True, exist_ok=True)
        self.aggregate_directory.mkdir(parents=True, exist_ok=True)

        # writing a project metadata json file
        json_write(self.results_directory / 'project.json',
                   {'project_name': self.project_name})

        # check if project metadata exists if its a different project?
        # if it does create one and update metadata

        # check the current location of solutions
        # if there are solution it updates the track of the
        # location and info about these solutions

        pass

    def add_solution(self, setup: SUPPORTED_ANALYSIS,
                     result: BaseSimulationOutput, add_tag: bool = False):

        tag = self.tag if add_tag else {}

        solution = Solution(
            result=result.flatten(),
            setup=setup,
            build_parameters=tag,
            metadata=Metadata(date=datetime.now())
        )

        # solution = Solution.model_validate(solution)
        serialized_solution = solution.model_dump_json(indent=4)

        write(self.solutions_directory / 'sol.json', serialized_solution)

    def load_tag(self, tag: dict, title: str):
        self.tag = tag

    # def _generate_all_solutions(self) -> Iterable[tuple[SUPPORTED_ANALYSIS, dict, dict]]:
    #
    #     json_files = self.solutions_directory.glob('*.json')
    #     json_files = sorted(json_files, key=lambda x: x.lstat().st_mtime)
    #
    #     for f in json_files:
    #         data = read(f)
    #         yield Solution.model_validate_json(data)

    @validate_call
    def _take_first_n_solutions(self, solutions: Iterable[Solution],
                                number_of_solutions: POSITIVE_INTEGER | None = None) -> Iterable[Solution]:
        return islice(solutions, number_of_solutions)

    def _generate_solutions_jsons(self):
        # generating jsons from the latest to the oldest
        json_files = self.solutions_directory.glob('*.json')
        return sorted(json_files, key=lambda x: x.lstat().st_mtime, reverse=True)

    def _generate_solutions(self) -> Iterable[Solution]:

        for f in self._generate_solutions_jsons():
            data = read(f)
            yield Solution.model_validate_json(data)

    @validate_call
    def get_solutions(self,
                      setup_discriminator: SimulationTypesNames | None = None,
                      build_parameters_discriminator: dict | None = None,
                      number_of_solutions: POSITIVE_INTEGER | None = None) -> list[Solution]:

        """
        Support couples of different options:
        1. get solution by setup class -> given a supported analysis return the most
            recent solution that matches to it
        2. get solution without setup class -> then maybe just return all
            the solutions given number of solutions wanted
        """

        # first get the all the solutions (this is a generator). they are sorted from the most recent to the least
        solutions = self._generate_solutions()

        # discriminate against setup name and build parameters
        solutions = filter(lambda x: x.discriminate(setup_discriminator, build_parameters_discriminator), solutions)

        # taking only the first ones that matching our conditions
        solutions = self._take_first_n_solutions(solutions, number_of_solutions)

        # retuning list of the solutions
        return list(solutions)

        # # filter only relevant designs
        # # solutions = filter(lambda x: x[0].design_name == design_name, solutions)
        #
        # # now if tag filter by tag
        # if setup_name:
        #     solutions = filter(lambda x: x[0].setup_name == setup_name, solutions)
        #
        # if tag:
        #     solutions = filter(lambda x: x[2] == tag, solutions)
        #
        # return list(solutions)

    def _filter_solutions(self, filter_func):
        pass

    def get_solution(self,
                     setup_discriminator: SimulationTypesNames | None = None,
                     build_parameters_discriminator: dict | None = None) -> Solution | None:

        solutions = self.get_solutions(setup_discriminator, build_parameters_discriminator, number_of_solutions=1)
        if not solutions or len(solutions) == 0:
            return
        return solutions[0]

    def aggregate(self) -> tuple[SimulationTypesNames, dict]:

        # get all solutions
        solutions = self._generate_solutions()

        # sort them by setup type
        solutions = sorted(solutions, key=lambda x: x.setup.type)

        # group by discrimination of the setup type
        for k, v in groupby(solutions, lambda x: x.setup.type):
            # order the group by time
            v = list(v)

            sorted_solutions = sorted(v, key=lambda x: x.metadata.date)

            # load result and call for flatten
            flat_solutions = map(lambda x: x.flatten(), sorted_solutions)

            yield k, flat_solutions

    def aggregate_and_save(self):
        # create aggregation folder
        for setup_type, data in self.aggregate():
            df = DataFrame(data)
            df.to_csv(self.aggregate_directory / f'{setup_type}.csv', index=False)
