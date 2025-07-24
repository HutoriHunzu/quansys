"""
Submit command - lightweight signature only, heavy logic in impl.py
"""
import typer
from pathlib import Path

def submit(
        config_path: Path = typer.Argument(..., help="Path to the config.yaml file."),
        venv: str = typer.Argument(..., help="Name of the conda virtual environment to be activated"),
        name: str = typer.Option(..., "--name", "-n", help="Project name for the workflow."),
        files: list[Path] = typer.Option(None, "--files", "-f", help="Additional files to copy."),
        mem: int = typer.Option(120000, "--mem", "-m", help="Total memory required in MB."),
        timeout: str = typer.Option("03:00", "--timeout", "-t", help="Job duration in HH:MM format."),
        prepare: bool = typer.Option(False, "--prepare", "-p", help="Only prepare the job without submitting."),
        overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite the existing project folder."),
):
    """
    Prepare and optionally submit a simulation workflow to the cluster.
    """
    # Lazy import the heavy implementation only when command is actually called
    from .impl import execute_submit
    
    return execute_submit(
        config_path=config_path,
        venv=venv,
        name=name,
        files=files,
        mem=mem,
        timeout=timeout,
        prepare=prepare,
        overwrite=overwrite
    )