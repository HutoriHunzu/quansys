from ansys.aedt.core.hfss import Hfss
from typing import List, Iterable
from pathlib import Path

from .config_handler import Config, ConfigProject, ConfigJunction, ConfigSweep, ModesAndLabels, ValuedVariable

from .classical_simulation import classical_run
from .quantum_simulation import quantum_run
from .hfss_common import variable_handler
from .json_utils import json_write, unique_name_by_counter


def main(config: Config):
    # check status

    config_project = config.config_project
    with Hfss(version=config_project.version, new_desktop=False,
              design=config_project.design_name, project=config_project.execution_dir / config_project.path,
              close_on_exit=True, remove_lock=True, non_graphical=config_project.non_graphical) as hfss:
        # check for build
        for build_params in config.builder.build(hfss, config_project):
            #

            _analyze_sweep(hfss,
                           config_project,
                           junctions=config.junctions,
                           modes_and_labels_lst=config.modes_and_labels,
                           hfss_sweep=config.sweep,
                           tag_key=build_params)

        # _analysis(hfss, config)


def _analysis(hfss: Hfss, config: Config):
    # change variables accordingly
    variable_handler.set_variables(hfss, config.hfss_variables)

    # call for classical simulation
    mode_to_freq_and_q_factor = classical_run(hfss, config.config_project)
    json_write('classical_results.json', mode_to_freq_and_q_factor)

    # save results
    for modes_and_labels in config.modes_and_labels:
        mode_to_labels = modes_and_labels.parse(mode_to_freq_and_q_factor)

        # call for quantum simulation
        quantum_result = quantum_run(hfss, mode_to_labels, config.junctions)

        # infer name
        result_name = '_'.join(mode_to_labels.values())
        json_write(f'{result_name}.json', quantum_result)


def _analyze_single_variation(hfss: Hfss,
                              config_project: ConfigProject,
                              junctions: List[ConfigJunction] | None = None,
                              modes_and_labels_lst: List[ModesAndLabels] | None = None,
                              hfss_variables: Iterable[ValuedVariable] | None = None,
                              tag_key: dict | None = None
                              ):
    if tag_key is None:
        tag_key = dict()

    if hfss_variables:
        # change variables accordingly
        variable_handler.set_variables(hfss, hfss_variables)
        variables_as_dict = dict(map(lambda x: (x.name, x.to_string()), hfss_variables))
        tag_key = dict(**tag_key, **variables_as_dict)


    json_write(config_project.execution_dir / 'tag.json', tag_key)

    # call for classical simulation
    mode_to_freq_and_q_factor = classical_run(hfss, config_project)
    json_write(config_project.execution_dir / 'classical_results.json', mode_to_freq_and_q_factor)

    # write project
    # export profile and convergence
    variation = ' '.join(map(lambda x: f'{x[0]}={x[1].evaluated_value}', hfss.variable_manager.variables.items()))
    # print(variation)

    prof_path = str(unique_name_by_counter(Path('profile.prof')).resolve())
    conv_path = str(unique_name_by_counter(Path('convergence.conv')).resolve())
    variables_path = str(unique_name_by_counter(Path('variables.csv')).resolve())
    hfss.export_profile('Setup1', variation=variation, output_file=config_project.execution_dir / prof_path)
    hfss.export_convergence('Setup1', variations=variation, output_file=config_project.execution_dir / conv_path)
    hfss.export_variables_to_csv(variables_path)

    if not (junctions and modes_and_labels_lst):
        return

    # save results
    for modes_and_labels in modes_and_labels_lst:
        mode_to_labels = modes_and_labels.parse(mode_to_freq_and_q_factor)

        # call for quantum simulation
        quantum_result = quantum_run(hfss, mode_to_labels, junctions)

        # infer name
        result_name = '_'.join(mode_to_labels.values())
        json_write(config_project.execution_dir / f'{result_name}.json', quantum_result)


def _analyze_sweep(hfss: Hfss,
                   config_project: ConfigProject,
                   junctions: List[ConfigJunction] | None = None,
                   modes_and_labels_lst: List[ModesAndLabels] | None = None,
                   hfss_sweep: ConfigSweep | None = None,
                   tag_key: dict | None = None
                   ):
    # for each group of parameters do single analysis
    if hfss_sweep is None:
        return _analyze_single_variation(hfss, config_project, junctions, modes_and_labels_lst,
                                         tag_key=tag_key)

    for variation in hfss_sweep.generate_variation():
        _analyze_single_variation(hfss, config_project, junctions, modes_and_labels_lst,
                                  hfss_variables=variation,
                                  tag_key=tag_key)
