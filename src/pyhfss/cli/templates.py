from pyhfss import WorkflowConfig


def generate_job_submission_script(results_dir, config: WorkflowConfig, mem_mb, timeout,
                                   default_cores=8):
    """
    Generate the job_submission.sh script.
    """
    # try to look for cores in all simulations and take the maximum
    core_lst = map(lambda x: x.cores if hasattr(x, 'cores') else 1, config.simulations.values())
    cores = max(default_cores, max(core_lst))

    project_name = results_dir.stem
    results_dir = results_dir.resolve()  # Ensure full path

    job_script = results_dir / "job_submission.sh"

    template = f"""#!/bin/bash
bsub -J {project_name} \\
    -q short \\
    -oo {results_dir}/lsf_output_%J.log \\
    -eo {results_dir}/lsf_error_%J.err \\
    -n {cores} \\
    -W {timeout} \\
    -R "rusage[mem={mem_mb // cores}] span[hosts=1]" \\
    -cwd {results_dir} \\
    {results_dir}/simulation_script.sh
    """
    job_script.write_text(template)


def generate_simulation_script(results_dir, venv):
    """
    Generate the simulation_script.sh script and set execute permissions.
    """
    simulation_script = results_dir / "simulation_script.sh"
    config_path = (results_dir / "config.yaml").resolve()

    template = f"""#!/bin/bash
module load ANSYS/Electromagnetics242
source /apps/easybd/programs/miniconda/24.9.2_environmentally/etc/profile.d/conda.sh
module load miniconda/24.9.2_environmentally
conda activate {venv}
workflow run-flow {config_path}
    """
    simulation_script.write_text(template)

    # Set execute permissions for the script
    simulation_script.chmod(0o755)

