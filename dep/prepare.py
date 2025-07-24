

def prepare_job(config_path, project_dir, files, mem, timeout, venv):
    # Use cached imports for better performance
    from .cache import cached_import
    from .utils import copy_files
    from .templates import generate_job_submission_script, generate_simulation_script
    
    WorkflowConfig = cached_import('quansys.workflow', attr_name='WorkflowConfig')
    
    """
    Prepare the workflow: create directories, copy files, generate scripts.
    """
    # Create the project directory
    config = WorkflowConfig.load_from_yaml(config_path)
    project_dir.mkdir(parents=True, exist_ok=True)

    # Save updated config.yaml to the project directory
    config_path = project_dir / "config.yaml"
    config.save_to_yaml(config_path)

    # Combine builder files with CLI-specified files
    if files is not None:
        copy_files(files, project_dir)

    # Generate cluster scripts
    generate_job_submission_script(project_dir, config, mem, timeout)
    generate_simulation_script(project_dir, venv)

    return project_dir.resolve()

