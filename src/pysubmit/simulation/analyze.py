from ansys.aedt.core.hfss import Hfss
from typing import List, Iterable
from pathlib import Path

from .config_handler import Config, ConfigProject, ConfigJunction, ConfigSweep, ModesAndLabels, ValuedVariable
from .config_handler.builder_scheme import Builder

from .classical_simulation import ANALYSIS_ADAPTER
from .quantum_simulation import quantum_run
from .hfss_common import variable_handler
# from .json_utils import json_write, unique_name_by_counter
from pysubmit.simulation.data_handler.data_handler import HDF5Handler
from session_handler.session import start_hfss_session


def main(config: Config):
    # initialize a file to save data
    handler = HDF5Handler('data.h5', config.name)

    with start_hfss_session(config.session_parameters) as hfss:

        builder = config.builder

        for builder_interface in builder.build(hfss, handler):
            # calling for sweep if necessary

            pass

        pass

    # build phase
    # essentially support different approaches to builds
    # eventually should result in having a working design and a setup
    # should be in the following form:
    # design name, setup name

    # sweep support for the build phase can be in two parts:
    # either part of the build phase itself
    # of as a hook before running the analysis

    # in summary:
    # build phase options should be:
    # function(hfss, args: dict) --> Iterable[design_name, setup_name]

    # variables settings
    # initialize setups?
    # check status

    config_project = config.config_project

    builder = Builder(config.config_builder)

    with Hfss(version=config_project.version, new_desktop=False,
              design=config_project.design_name, project=str(Path(config_project.path).resolve()),
              close_on_exit=True, remove_lock=True, non_graphical=config_project.non_graphical) as hfss:
        # check for build

        for setup, build_tag in builder.yield_design(hfss):
            #

            _analyze_sweep(hfss,
                           setup,
                           config_project,
                           handler,
                           junctions=config.junctions,
                           modes_and_labels_lst=config.modes_and_labels,
                           hfss_sweep=config.sweep,
                           tag_key=build_tag)

        # _analysis(hfss, config)


#
# def _analysis(hfss: Hfss, config: Config):
#     # change variables accordingly
#     variable_handler.set_variables(hfss, config.hfss_variables)
#
#     # call for classical simulation
#     mode_to_freq_and_q_factor = classical_run(hfss, config.config_project)
#     json_write('classical_results.json', mode_to_freq_and_q_factor)
#
#     # save results
#     for modes_and_labels in config.modes_and_labels:
#         mode_to_labels = modes_and_labels.parse(mode_to_freq_and_q_factor)
#
#         # call for quantum simulation
#         quantum_result = quantum_run(hfss, mode_to_labels, config.junctions)
#
#         # infer name
#         result_name = '_'.join(mode_to_labels.values())
#         json_write(f'{result_name}.json', quantum_result)


def _analyze_single_variation(hfss: Hfss,
                              setup_type: str,
                              setup,
                              config_project: ConfigProject,
                              handler: HDF5Handler,
                              junctions: List[ConfigJunction] | None = None,
                              modes_and_labels_lst: List[ModesAndLabels] | None = None,
                              hfss_variables: Iterable[ValuedVariable] | None = None,
                              tag_key: dict | None = None
                              ):
    handler.create_new_iteration()

    if tag_key is None:
        tag_key = dict()

    if hfss_variables:
        # change variables accordingly
        variable_handler.set_variables(hfss, hfss_variables)
        variables_as_dict = dict(map(lambda x: (x.name, x.to_string()), hfss_variables))
        tag_key = dict(**tag_key, **variables_as_dict)

    # writing tag
    handler.add_data('tag', tag_key)

    # creating analysis
    analysis_parameters = {'type': setup_type,
                           'hfss': hfss,
                           'config_project': config_project,
                           'setup': setup}

    analysis_instance = ANALYSIS_ADAPTER.validate_python(**analysis_parameters)

    # make analysis
    analysis_instance.analyze()

    # get results
    format_name, data = analysis_instance.format()

    # save results
    handler.add_data(format_name, data)

    if not (junctions and modes_and_labels_lst):
        return

    # save results
    for modes_and_labels in modes_and_labels_lst:
        mode_to_labels = modes_and_labels.parse(mode_to_freq_and_q_factor)

        # call for quantum simulation
        quantum_result = quantum_run(hfss, mode_to_labels, junctions)

        # infer name
        result_name = '_'.join(mode_to_labels.values())
        handler.add_data('quantum_epr', quantum_result)
        # json_write(config_project.execution_dir / f'{result_name}.json', quantum_result)


def _analyze_sweep(hfss: Hfss,
                   setup,
                   config_project: ConfigProject,
                   handler: HDF5Handler,
                   junctions: List[ConfigJunction] | None = None,
                   modes_and_labels_lst: List[ModesAndLabels] | None = None,
                   hfss_sweep: ConfigSweep | None = None,
                   tag_key: dict | None = None
                   ):
    # for each group of parameters do single analysis
    if hfss_sweep is None:
        return _analyze_single_variation(hfss, setup, config_project, handler, junctions, modes_and_labels_lst,
                                         tag_key=tag_key)

    for variation in hfss_sweep.generate_variation():
        _analyze_single_variation(hfss, setup, config_project, handler, junctions, modes_and_labels_lst,
                                  hfss_variables=variation,
                                  tag_key=tag_key)
