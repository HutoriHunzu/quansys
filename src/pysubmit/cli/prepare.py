from pathlib import Path
from .utils import generate_timestamp, copy_files
from .templates import generate_job_submission_script, generate_simulation_script

def prepare_job(config, files, mem):
    """
    Prepare the workflow: create directories, copy files, generate scripts.
    """
    # Create results directory
    timestamp = generate_timestamp()
    project_name = config.data_parameters.project_name
    results_dir = Path(f"{project_name}/{timestamp}/all_data")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Save updated config.yaml to results directory
    config.save_to_yaml(results_dir / "config.yaml")

    # Collect files to copy
    builder_files = []
    if config.builder and config.builder.type == "script_builder":
        # Collect builder path and additional files
        builder_files.append(config.builder.path)
        if config.builder.additional_files:
            builder_files.extend(config.builder.additional_files)

    # Combine builder files with CLI-specified files
    all_files_to_copy = builder_files + (files or [])
    copy_files(all_files_to_copy, results_dir)

    # Generate cluster scripts
    generate_job_submission_script(results_dir, config, mem)
    generate_simulation_script(results_dir)

    return results_dir
