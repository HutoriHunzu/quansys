from pathlib import Path

from importlib.resources import files, as_file
from quansys import examples
import shutil


def copy_example_file(name: str, dest: Path):
    src = as_file(files(examples) / name)
    with src as f:
        if not f.exists():
            raise FileNotFoundError(f"Missing example file: {f}")
        shutil.copy(f, dest / name)


def copy_example_files(example_type: str = "simple", with_config: bool = True, destination: Path = Path.cwd()):
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
        copy_example_file(filename, target_path)
        copied_paths.append(target_path)

    return copied_paths


if __name__ == "__main__":
    # Example usage
    copy_example_file('simple_config.yaml', Path.cwd() / 'example_config.yaml')
