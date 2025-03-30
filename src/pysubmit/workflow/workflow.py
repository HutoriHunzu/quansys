from .builder import SUPPORTED_BUILDERS
from .session_handler import start_hfss_session, SessionParameters
from .config import WorkflowConfig
from .data_handler import DataHandler
from .sweep import chain_sweeps
from ..simulation import SUPPORTED_ANALYSIS


def execute_workflow(config: WorkflowConfig) -> None:
    """
    Execute the entire HFSS workflow based on a given configuration.

    1. Create folders for storing data.
    2. Start an HFSS session.
    3. Optionally run a builder phase (with or without sweeps).
    4. For each set of builder parameters, create an iteration, store them, and run simulations.
    5. (Commented out) Optionally call `aggregate_and_save` to aggregate results at the end.

    Args:
        config (WorkflowConfig): The workflow configuration object containing:
            - HFSS session parameters
            - Simulation definitions
            - Data handling configuration
            - Builder definitions
            - Builder sweeps
    """
    # Prepare data handler
    data_handler = config.data_handler
    data_handler.create_folders()

    # Start HFSS session
    with start_hfss_session(config.session_parameters) as hfss:
        # Run build phase
        for build_parameters in _generate_build_parameters(
            config.builder, config.builder_sweep, hfss
        ):
            # Create an iteration folder for each set of build parameters
            data_handler.create_iteration()
            data_handler.add_data_to_iteration("build_parameters", build_parameters)

            # Run all simulations in this iteration
            _execute_simulations(config.simulations, hfss, data_handler)

    # Aggregation according to grouping configuration
    data_handler.aggregate_and_save()


def _generate_build_parameters(builder, sweeps, hfss):
    """
    Generate a series of build parameter dictionaries by chaining sweeps.

    If no sweeps are defined, yields a single empty dictionary.

    Args:
        builder (SUPPORTED_BUILDERS | None): The optional builder.
        sweeps (list[SUPPORTED_SWEEPS] | None): A list of sweep definitions, or None.
        hfss: An active HFSS instance from which we can set or update designs.

    Yields:
        dict: A dictionary of parameters for the builder to apply.
    """
    if sweeps is None:
        # No sweeps, just yield empty parameters
        build_params_list = [{}]
    else:
        # Chain multiple sweeps into a sequence of parameter dictionaries
        build_params_list = chain_sweeps(sweeps)

    for build_params in build_params_list:
        if builder is not None:
            # Apply the builder with these parameters
            builder.build(hfss, parameters=build_params)

        yield build_params


def _execute_simulations(
    simulations: dict[str, SUPPORTED_ANALYSIS],
    hfss,
    data_handler: DataHandler
) -> None:
    """
    Run a dictionary of simulations, store their results, and optionally store each report.

    Args:
        simulations (dict[str, SUPPORTED_ANALYSIS]):
            A dictionary with simulation ID (key) and the simulation object (value).
        hfss:
            The active HFSS session to run each simulation on.
        data_handler (DataHandler):
            Manages saving simulation outputs to disk.
    """
    # First, register all simulation identifiers for this iteration
    for sim_id, simulation in simulations.items():
        data_handler.register_identifier(sim_id)

    # Now, run each simulation and store results
    for sim_id, simulation in simulations.items():
        # Run the simulation
        result = simulation.analyze(hfss=hfss, data_handler=data_handler)

        # Store the simulation results in JSON
        data_handler.add_data_to_iteration(sim_id, result.model_dump())

        # Optionally get a "report" object and store it as well
        report = simulation.report()
        if report is not None:
            report_id = f"{sim_id}_report"
            data_handler.add_data_to_iteration(report_id, report.model_dump())
