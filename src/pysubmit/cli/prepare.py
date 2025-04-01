from pathlib import Path
from pysubmit.workflow import WorkflowConfig
from .utils import copy_files
from .templates import generate_job_submission_script, generate_simulation_script

def prepare_job(config: WorkflowConfig, files, mem, timeout):
    """
    Prepare the workflow: create directories, copy files, generate scripts.
    """
    # Create the project directory
    project_dir = Path(config.data_handler.root_directory)
    project_dir.mkdir(parents=True, exist_ok=True)

    # Save updated config.yaml to the project directory
    config_path = project_dir / "config.yaml"
    config.save_to_yaml(config_path)

    # Copy files (builder.path, additional files)
    builder_files = []
    if config.builder and config.builder.type == "script_builder":
        # Collect builder path and additional files
        builder_files.append(config.builder.path.resolve())
        if config.builder.additional_files:
            builder_files.extend([f.resolve() for f in config.builder.additional_files])

    # Combine builder files with CLI-specified files
    all_files_to_copy = builder_files + (files or [])
    copy_files(all_files_to_copy, project_dir)

    # Generate cluster scripts
    generate_job_submission_script(project_dir, config, mem, timeout)
    generate_simulation_script(project_dir)

    return project_dir.resolve()

