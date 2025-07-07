from .session_handler import open_pyaedt_file, PyaedtFileParameters
from .config import WorkflowConfig
from ..simulation import SIMULATION_RESULTS_ADAPTER
from pykit.project import Project
from pykit.save import save_json
from pykit.aggregator import Aggregator

import pandas as pd

import shutil


def execute_workflow(config: WorkflowConfig) -> None:

    project = Project(root=config.root_folder)
    iteration_proj = project.sub('iterations')

    for params in config.builder_sweep.generate():

        pyaedt_parameters = _build_phase(config.builder,
                                         params,
                                         config.pyaedt_file_parameters,
                                         iteration_proj)

        with open_pyaedt_file(pyaedt_parameters) as hfss:

            _simulations_phase(
                config.simulations,
                params,
                hfss,
                iteration_proj
            )

    aggregation_proj = project.sub('aggregations')
    for name, aggregator in config.aggregation_dict.items():

        _aggregation_phase(name, aggregator, aggregation_proj)


def _build_phase(builder,
                 params: dict,
                 pyaedt_file_parameters: PyaedtFileParameters,
                 project: Project) -> PyaedtFileParameters:
    session = project.session('build', params=params)

    # copying the instance of pyaedt file parameters
    pyaedt_file_parameters = pyaedt_file_parameters.model_copy()

    # check if status is done
    if session.is_done():
        hfss_path = session.files['hfss']
        pyaedt_file_parameters.file_path = hfss_path
        return pyaedt_file_parameters

    session.start()

    # creating new path for the hfss file and copying the file there
    aedt_file_path = session.path('hfss.aedt')
    shutil.copy(pyaedt_file_parameters.file_path, aedt_file_path)
    pyaedt_file_parameters.file_path = aedt_file_path

    # copy file to session
    with open_pyaedt_file(pyaedt_file_parameters) as hfss:
        builder.build(hfss, parameters=params)

    session.done()

    return pyaedt_file_parameters


def _simulations_phase(identifier_simulation_dict,
                       params: dict,
                       hfss,
                       project: Project):


    for identifier, simulation in identifier_simulation_dict.items():

        session = project.session(identifier, params=params)

        if session.is_done():
            continue

        session.start()

        result = simulation.analyze(hfss=hfss)
        path = session.path('.json')

        save_json(path, result.model_dump())
        session.attach_files({'data': path})

        session.done()


def _aggregation_phase(identifier_aggregator_dict: dict[str, Aggregator], relpath, project: Project):

    # for identifier, aggregator
    for identifier, agg in identifier_aggregator_dict.items():
        session = project.session(identifier=identifier)

        session.start()

        results = agg.aggregate(project.ledger, 'data', relpath=relpath, adapter=SIMULATION_RESULTS_ADAPTER)

        path = session.path('.csv')

        pd.DataFrame(results).to_csv(path)

        session.attach_files({'data': path})

        session.done()


