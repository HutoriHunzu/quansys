# workflow.py
from pathlib import Path
import shutil
import pandas as pd

from .session_handler import PyaedtFileParameters
from .config import WorkflowConfig
from .prepare import PrepareFolderConfig
from ..simulation import SIMULATION_RESULTS_ADAPTER

from pykit.project import Project
from pykit.save import save_json
from pykit.aggregator import Aggregator


# ---------------------------------------------------------------------------
# public entry-point
# ---------------------------------------------------------------------------
def execute_workflow(config: WorkflowConfig) -> None:
    """
    Drive the complete HFSS experiment workflow.

    Phases: prepare  →  build  →  simulations  →  aggregations
    """
    project = Project(root=config.root_folder)
    iteration_proj = project.sub("iterations")

    for params in config.builder_sweep.generate():

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
        with run_params.open_pyaedt_file() as hfss:
            _simulations_phase(
                config.simulations,
                params,
                hfss,
                iteration_proj,
            )

    # 4. AGGREGATION
    aggregation_proj = project.sub("aggregations")
    for name, aggregator in config.aggregation_dict.items():
        _aggregation_phase(name, aggregator, aggregation_proj)


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
    if not cfg.copy_enabled:
        return pyaedt

    session = project.session("prepare", params=params)
    dest: Path = session.path(cfg.dest_name)

    # Idempotent: if copy already exists, reuse it
    if dest.exists():
        return pyaedt.model_copy(update={"file_path": dest})

    # Template missing -> just fall through without copy
    if not pyaedt.file_path.exists():
        return pyaedt

    # Perform streaming copy (preserves metadata, low RAM)
    shutil.copy2(pyaedt.file_path, dest)
    return pyaedt.model_copy(update={"file_path": dest})


def _build_phase(builder, pyaedt_params, params, project):
    session = project.session("build", params=params)
    if session.is_done():
        return

    session.start()
    with pyaedt_params.open_pyaedt_file() as hfss:
        builder.build(hfss, session, parameters=params)
    session.done()


def _simulations_phase(identifier_simulation_dict, params, hfss, project):
    for identifier, simulation in identifier_simulation_dict.items():
        session = project.session(identifier, params=params)
        if session.is_done():
            continue

        session.start()
        result = simulation.analyze(hfss=hfss)
        path = session.path(".json")
        save_json(path, result.model_dump())
        session.attach_files({"data": path})
        session.done()


def _aggregation_phase(name: str, aggregator: Aggregator, project: Project):
    session = project.session(identifier=name)
    if session.is_done():
        return

    session.start()
    results = aggregator.aggregate(
        project.ledger,
        "data",
        relpath=project.relpath,
        adapter=SIMULATION_RESULTS_ADAPTER,
    )
    path = session.path(".csv")
    pd.DataFrame(results).to_csv(path)
    session.attach_files({"data": path})
    session.done()
