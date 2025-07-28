# workflow.py
from pathlib import Path
import shutil
import pandas as pd

from .session_handler import PyaedtFileParameters
from .config import WorkflowConfig
from .prepare import PrepareFolderConfig
from ..simulation import SIMULATION_RESULTS_ADAPTER

from pykit.project import Project, StorageMode
from pykit.sweeper import ChainSweep
from pykit.save import save_json
from pykit.aggregator import Aggregator


# ---------------------------------------------------------------------------
# public entry-point
# ---------------------------------------------------------------------------
def execute_workflow(config: WorkflowConfig) -> None:
    """
    Run a complete, cached HFSS experiment workflow.

    The engine performs four deterministic phases:

    1. **Prepare** – create an isolated results folder and, if requested,
       copy the template ``.aedt`` project into it.
    2. **Build** – apply the current sweep parameters to the HFSS design
       through the configured builder object.
    3. **Simulate** – execute one or more analyses for every parameter set
       and store their JSON results.
    4. **Aggregate** – flatten and merge selected results into CSV files
       for downstream analysis.

    Args:
        config (WorkflowConfig):
            Parsed workflow definition.
            See the full field reference in
            [`api/workflow_config.md`](../api/workflow_config.md).

    Returns:
        None

    Raises:
        ValueError: If the configuration is incomplete.
        RuntimeError: If an HFSS session cannot be opened or a simulation
            fails unexpectedly.

    Example:
        ```python
        from pathlib import Path
        from quansys.workflow import (
            WorkflowConfig, PyaedtFileParameters,
            DesignVariableBuilder, execute_workflow
        )
        from quansys.simulation import EigenmodeAnalysis
        from pykit.sweeper import DictSweep

        cfg = WorkflowConfig(
            pyaedt_file_parameters=PyaedtFileParameters(
                file_path=Path("resources/simple_design.aedt"),
                non_graphical=True
            ),
            builder=DesignVariableBuilder(design_name="my_design"),
            builder_sweep=[DictSweep(parameters={"chip_base_width": ["3 mm", "4 mm"]})],
            simulations={
                "classical": EigenmodeAnalysis(setup_name="Setup1",
                                               design_name="my_design")
            },
            aggregation_dict={"classical_agg": ["classical"]}
        )

        execute_workflow(cfg)
        # → results/aggregations/classical_agg.csv is produced
        ```
    """
    project = Project(root=config.root_folder)
    iteration_proj = project.sub("iterations")

    chain_sweep = ChainSweep(sweepers=config.builder_sweep)

    for params in chain_sweep.generate():

        # 1. PREPARE (copy template .aedt if policy allows)
        run_params = _prepare_folder_phase(
            cfg=config.prepare_folder,
            pyaedt=config.pyaedt_file_parameters,
            params=params,
            project=iteration_proj,
        )

        # 2. BUILD (apply parameter sweep values)
        _build_phase(config.builder, run_params, params, iteration_proj)

        # 3. SIMULATIONS
        _simulations_phase(
            config.simulations,
            params,
            run_params.model_copy(),
            config.keep_hfss_solutions,
            iteration_proj
        )

    # 4. AGGREGATION
    aggregation_proj = project.sub("aggregations")
    for name, identifiers in config.aggregation_dict.items():
        aggregator = Aggregator(identifiers=identifiers)
        _aggregation_phase(name, aggregator, aggregation_proj, iteration_proj)


# ---------------------------------------------------------------------------
# helper phases
# ---------------------------------------------------------------------------
def _prepare_folder_phase(
    cfg: PrepareFolderConfig,
    pyaedt: PyaedtFileParameters,
    params: dict,
    project: Project,
) -> PyaedtFileParameters:
    """
    • Optionally copy the template AEDT into the run folder.
    • Return a **new** PyaedtFileParameters whose file_path points at that copy.
    • Nothing is mutated in-place.
    """
    # ── skip entirely if policy disabled ────────────────────────────────────
    # if not cfg.copy_enabled:
    #     return pyaedt

    session = project.session("prepare", params=params)

    if session.is_done():
        hfss_path = session.files['hfss']
        return pyaedt.model_copy(update={"file_path": hfss_path})

    session.start()
    dest: Path = session.path(cfg.dest_name, include_identifier=False)

    # Template missing -> just fall through without copy
    if pyaedt.file_path.exists():
        shutil.copy2(pyaedt.file_path, dest)

    session.attach_files({'hfss': dest})

    session.done()
    return pyaedt.model_copy(update={"file_path": dest})


def _build_phase(builder, pyaedt_params, params, project):

    session = project.session("build", params=params)

    if session.is_done():
        return

    session.start()

    parameters_path = session.path('parameters.json')
    save_json(parameters_path, params)
    session.attach_files({'data': parameters_path})

    with pyaedt_params.open_pyaedt_file() as hfss:
        builder.build(hfss, parameters=params)
    session.done()


def _simulations_phase(identifier_simulation_dict,
                       params: dict,
                       run_params: PyaedtFileParameters,
                       keep_hfss_solutions: bool,
                       project: Project):

    designs = []

    for identifier, simulation in identifier_simulation_dict.items():
        session = project.session(identifier, params=params)
        if session.is_done():
            continue


        designs.append(simulation.design_name)

        run_params.design_name = simulation.design_name
        with run_params.open_pyaedt_file() as hfss:

            session.start()
            result = simulation.analyze(hfss=hfss)
            path = session.path(suffix=".json")
            save_json(path, result.model_dump())
            session.attach_files({"data": path})
            session.done()


    if not keep_hfss_solutions:
        with run_params.open_pyaedt_file() as hfss:
            for design_name in set(designs):
                hfss.set_active_design(design_name)
                hfss.cleanup_solution()


def _aggregation_phase(name: str, aggregator: Aggregator, project: Project, iteration_project: Project):
    session = project.session(identifier=name, storage_mode=StorageMode.PREFIX)
    if session.is_done():
        return

    session.start()
    results = aggregator.aggregate(
        project.ledger,
        "data",
        relpath=iteration_project.relpath,
        adapter=SIMULATION_RESULTS_ADAPTER,
    )
    path = session.path(suffix='.csv', include_uid=False)
    pd.DataFrame(results).to_csv(path)
    session.attach_files({"data": path})
    session.done()
