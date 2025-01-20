from .builder import SUPPORTED_BUILDERS
from .session_handler import start_hfss_session, SessionParameters
from .config import WorkflowConfig
from .data_handler import DataHandler
from .sweep import chain_sweeps


def execute_flow(config: WorkflowConfig):
    # establish a data handler
    data_handler = DataHandler(config.data_parameters)
    data_handler.prepare()

    # Starting a new session of HFSS
    with start_hfss_session(config.session_parameters) as hfss:
        ### BUILD PHASE ###
        for tag in _create_build_and_generate_tag(config.builder,
                                                  config.builder_sweep,
                                                  hfss,
                                                  data_handler):
            data_handler.load_tag(tag, 'build_parameters')

            ### SIMULATION PHASE ###
            _run_simulations(config.simulations, hfss, data_handler)

    data_handler.aggregate_and_save()


def _create_build_and_generate_tag(builder, sweeps, hfss, data_handler):
    if sweeps is None:
        lst_build_parameters = [{}]
    else:
        lst_build_parameters = chain_sweeps(sweeps)

    for build_parameters in lst_build_parameters:

        if builder:
            builder.build(hfss, parameters=build_parameters)

        yield build_parameters


def _run_simulations(simulations, hfss, data_handler):
    for sim in simulations:
        # result = sim.analyze_and_extract_results(hfss=hfss, data_handler=data_handler)
        result = sim.analyze(hfss=hfss, data_handler=data_handler)
        result_as_dict = sim.convert_result_to_dict(result)
        # converting result to dict
        data_handler.add_solution(sim, result_as_dict, add_tag=True)
