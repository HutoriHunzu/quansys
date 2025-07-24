"""
Submit command implementation - contains all heavy imports and logic
"""
import typer
from pathlib import Path
import shutil
import subprocess

def _copy_files(files, target_dir):
    """Copy a list of files to the target directory."""
    for file in files:
        if not Path(file).exists():
            raise FileNotFoundError(f"File not found: {file}")
        shutil.copy(file, target_dir)

def _generate_job_submission_script(results_dir, config, mem_mb, timeout, default_cores=8):
    """Generate the job_submission.sh script."""
    # try to look for cores in all simulations and take the maximum
    core_lst = map(lambda x: x.cores if hasattr(x, 'cores') else 1, config.simulations.values())
    cores = max(default_cores, max(core_lst))

    project_name = results_dir.stem
    results_dir = results_dir.resolve()  # Ensure full path
    simulation_script_path = (results_dir / 'simulation_script.sh').resolve()
    job_script = results_dir / "job_submission.sh"

    template = f"""#!/bin/bash
bsub -J {project_name} \\
    -q short \\
    -oo {(results_dir / 'lsf_output_%J.log')} \\
    -eo {(results_dir / 'lsf_error_%J.err')} \\
    -n {cores} \\
    -W {timeout} \\
    -R "rusage[mem={mem_mb // cores}] span[hosts=1]" \\
    -cwd {results_dir} \\
    {simulation_script_path}
    """
    job_script.write_text(template)

def _generate_simulation_script(results_dir, venv):
    """Generate the simulation_script.sh script and set execute permissions."""
    simulation_script = results_dir / "simulation_script.sh"
    config_path = (results_dir / "config.yaml").resolve()

    template = f"""#!/bin/bash
module load ANSYS/Electromagnetics242
source /apps/easybd/programs/miniconda/24.9.2_environmentally/etc/profile.d/conda.sh
module load miniconda/24.9.2_environmentally
conda activate {venv}
quansys run {config_path}
    """
    simulation_script.write_text(template)
    
    # Set execute permissions for the script
    simulation_script.chmod(0o755)

def _prepare_job(config_path, project_dir, files, mem, timeout, venv):
    """Prepare the workflow: create directories, copy files, generate scripts."""
    import quansys.workflow as workflow

    # Create the project directory
    config = workflow.WorkflowConfig.load_from_yaml(config_path)
    project_dir.mkdir(parents=True, exist_ok=True)

    # Save updated config.yaml to the project directory
    config_path = project_dir / "config.yaml" 
    config.save_to_yaml(config_path)

    # Copy additional files if specified
    if files is not None:
        _copy_files(files, project_dir)

    # Generate cluster scripts
    _generate_job_submission_script(project_dir, config, mem, timeout)
    _generate_simulation_script(project_dir, venv)

    return project_dir.resolve()

def _submit_job(results_dir):
    """Submit the job to the cluster using bsub."""
    job_script = results_dir / "job_submission.sh"
    if not job_script.exists():
        raise FileNotFoundError(f"{job_script} not found. Did you forget to prepare the job?")

    # Execute the job_submission.sh script
    subprocess.run(["bash", job_script], check=True)

def execute_submit(config_path, venv, name, files, mem, timeout, prepare, overwrite):
    """
    Main submit implementation - all heavy logic happens here.
    This function is only imported when the submit command is actually called.
    """
    # Define project directory
    project_dir = Path(name)

    # Remove the existing project folder if overwrite is enabled
    if project_dir.exists() and overwrite:
        typer.echo(f"Overwriting the existing project '{name}'...")
        shutil.rmtree(project_dir)

    # Prepare the job (heavy workflow imports happen here)
    results_dir = _prepare_job(config_path, project_dir, files, mem, timeout, venv)

    if prepare:
        typer.echo(f"Job prepared. Results directory: {results_dir}")
    else:
        # Submit the job
        _submit_job(results_dir)
        typer.echo(f"Job submitted. Results directory: {results_dir}")