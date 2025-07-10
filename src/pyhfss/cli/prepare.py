from pathlib import Path
from pyhfss.workflow import WorkflowConfig
from .utils import copy_files
from .templates import generate_job_submission_script, generate_simulation_script

def prepare_job(config: WorkflowConfig, project_dir, files, mem, timeout, venv):
    """
    Prepare the workflow: create directories, copy files, generate scripts.
    """
    # Create the project directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Save updated config.yaml to the project directory
    config_path = project_dir / "config.yaml"
    config.save_to_yaml(config_path)

    # Combine builder files with CLI-specified files
    copy_files(files, project_dir)

    # Generate cluster scripts
    generate_job_submission_script(project_dir, config, mem, timeout)
    generate_simulation_script(project_dir, venv)

    return project_dir.resolve()

