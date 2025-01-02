from ansys.aedt.core.hfss import Hfss
from ansys.aedt.core.modules.setup_templates import HFSSDrivenAuto
from typing import List, Iterable
from pathlib import Path

from .config_handler import Config, ConfigProject, ConfigJunction, ConfigSweep, ModesAndLabels, ValuedVariable
from .config_handler.builder_scheme import Builder

from .classical_simulation import run_eigenmode, run_driven_model
from .quantum_simulation import quantum_run
from .hfss_common import variable_handler
# from .json_utils import json_write, unique_name_by_counter
from ..shared.data_handler import HDF5Handler

import h5py


def main(config: Config):
    # initialize a file to save data
    handler = HDF5Handler('data.h5', config.name)

    # build phase
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
    # json_write(Path('tag.json'), tag_key)

    # check if it is driven model or not
    if setup.props['SetupType'] == 'HfssDrivenAuto':
        freq_to_s_parameter = run_driven_model(hfss, setup, config_project)
        handler.add_data('s_11_parameter', freq_to_s_parameter)

        # json_write(Path('classical_results.json'), freq_to_s_parameter)
        return

    # call for classical simulation
    mode_to_freq_and_q_factor = run_eigenmode(hfss, setup, config_project)
    # json_write(Path('classical_results.json'), mode_to_freq_and_q_factor)
    handler.add_data('eigenmode', mode_to_freq_and_q_factor)
    # json_write(Path('classical_results.json'), mode_to_freq_and_q_factor)

    # write project
    # export profile and convergence
    # variation = ' '.join(map(lambda x: f'{x[0]}={x[1].evaluated_value}', hfss.variable_manager.variables.items()))
    # prof_path = str(unique_name_by_counter(Path('profile.prof')).resolve())
    # conv_path = str(unique_name_by_counter(Path('convergence.conv')).resolve())
    # variables_path = str(unique_name_by_counter(Path('variables.csv')).resolve())
    # hfss.export_profile(setup.name, variation=variation, output_file=prof_path)
    # hfss.export_convergence(setup.name, variations=variation, output_file=conv_path)
    # hfss.export_variables_to_csv(variables_path)

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
