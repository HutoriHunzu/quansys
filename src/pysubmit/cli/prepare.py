from pathlib import Path
from .utils import generate_timestamp, copy_files
from .templates import generate_job_submission_script, generate_simulation_script

def prepare_job(config, files, mem, timeout):
    """
    Prepare the workflow: create directories, copy files, generate scripts.
    """
    from .templates import generate_job_submission_script, generate_simulation_script
    from .utils import generate_timestamp, copy_files

    # Create project directory with timestamp
    timestamp = generate_timestamp()
    project_dir = Path(config.data_parameters.project_name) / timestamp
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
    generate_job_submission_script(project_dir, config, mem * 1024, timeout)  # Convert GB to MB
    generate_simulation_script(project_dir)

    return project_dir.resolve()

