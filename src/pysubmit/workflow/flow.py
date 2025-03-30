from .builder import SUPPORTED_BUILDERS
from .session_handler import start_hfss_session, SessionParameters
from .config import WorkflowConfig
from .data_handler import DataHandler
from .sweep import chain_sweeps
from ..simulation import SUPPORTED_ANALYSIS


def execute_flow(config: WorkflowConfig):
    # establish a data handler
    data_handler = config.data_handler
    data_handler.create_folders()

    # Starting a new session of HFSS
    with start_hfss_session(config.session_parameters) as hfss:
        ### BUILD PHASE ###
        for build_parameters in _create_build_and_generate_tag(config.builder,
                                                               config.builder_sweep,
                                                               hfss,
                                                               data_handler):
            data_handler.create_iteration()

            data_handler.add_data_to_iteration('build_parameters', build_parameters)

            ### SIMULATION PHASE ###
            _run_simulations(config.simulations, hfss, data_handler)

    # data_handler.aggregate_and_save()


def _create_build_and_generate_tag(builder, sweeps, hfss, data_handler):
    if sweeps is None:
        lst_build_parameters = [{}]
    else:
        lst_build_parameters = chain_sweeps(sweeps)

    for build_parameters in lst_build_parameters:

        if builder:
            builder.build(hfss, parameters=build_parameters)

        yield build_parameters


def _run_simulations(simulations: dict[str, SUPPORTED_ANALYSIS], hfss, data_handler):
    # registering all simulations
    for identifier, sim in simulations.items():
        data_handler.register_identifier(identifier)

    # executing and saving simulations
    for identifier, sim in simulations.items():

        result = sim.analyze(hfss=hfss, data_handler=data_handler)

        data_handler.add_data_to_iteration(identifier, result.model_dump())

        report = sim.report()
        if report is not None:
            report_identifier = f'{identifier}_report'
            data_handler.register_identifier(report_identifier)
            data_handler.add_data_to_iteration(report_identifier, report.model_dump())
