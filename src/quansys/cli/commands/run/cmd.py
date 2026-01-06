"""
Run command - lightweight signature only, heavy logic in impl.py
"""

import typer
from pathlib import Path


def run(config_path: Path = typer.Argument(..., help="Path to the config.yaml file.")):
    """
    Load the config.yaml and execute the workflow.
    Updates the status file upon success or failure.
    """
    # Lazy import the heavy implementation only when command is actually called
    from .impl import execute_run

    return execute_run(config_path=config_path)
