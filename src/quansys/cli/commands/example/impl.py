"""
Example command implementation - contains all heavy imports and logic
"""
import typer
from pathlib import Path
import shutil
# import importlib

def _copy_example_file(name: str, dest: Path):
    """Copy a single example file to destination."""
    from importlib.resources import files, as_file

    # Import examples module directly
    import quansys.examples as examples

    src = as_file(files(examples) / name)
    with src as f:
        if not f.exists():
            raise FileNotFoundError(f"Missing example file: {f}")
        shutil.copy(f, dest / name)

def _copy_example_files(example_type: str = "simple", with_config: bool = True, destination: Path = Path.cwd()):
    """Copy example files based on type."""
    file_map = {
        "simple": ["simple_design.aedt", "simple_config.yaml"],
        "complex": ["complex_design.aedt", "complex_config.yaml"]
    }

    selected_files = file_map.get(example_type)
    if not selected_files:
        raise ValueError(f"Invalid example type: {example_type}")

    if not with_config:
        selected_files = [f for f in selected_files if f.endswith(".aedt")]

    copied_paths = []
    for filename in selected_files:
        target_path = destination / filename
        _copy_example_file(filename, target_path)
        copied_paths.append(target_path)

    return copied_paths

def execute_example(example_type, with_config):
    """
    Main example implementation - all heavy logic happens here.
    This function is only imported when the example command is actually called
    (and not for --list which exits early in cmd.py).
    """
    try:
        copied_files = _copy_example_files(example_type, with_config)
        for f in copied_files:
            typer.echo(f"Copied: {f}")
    except Exception as e:
        typer.echo(f"Failed to copy examples: {e}")
        raise typer.Exit(1)