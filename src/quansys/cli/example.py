from .utils import copy_files
from pathlib import Path


def copy_example_files(destination: Path = Path.cwd()):
    # Get the path to this file (e.g., src/quansys/cli/example.py)
    current_file = Path(__file__).resolve()

    # Navigate up to the root of the package (e.g., src/quansys)
    package_root = current_file.parent.parent.parent.parent

    # Locate the example files relative to that
    example_dir = package_root / "examples"

    config_path = example_dir / "config.yml"
    design_path = example_dir / "simple_design.aedt"

    # Ensure the files exist
    if not config_path.exists() or not design_path.exists():
        raise FileNotFoundError("One or more example files are missing.")

    # Copy them to the destination
    copy_files([config_path, design_path], destination)

    copied_files = [destination / config_path.name, destination / design_path.name]

    return copied_files
