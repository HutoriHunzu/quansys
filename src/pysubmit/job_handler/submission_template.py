from pathlib import Path
import subprocess


def write_sh_file(path: Path, txt: str, make_executable: bool = True):
    with open(path, 'w') as f:
        f.write(txt)

    if make_executable:
        path.chmod(path.stat().st_mode | 0o111)

    return path


def run_sh_file(path):
    # Now use subprocess to call submit_script.sh
    subprocess.run([path], check=True)


def get_simulation_script(path_to_run_file: Path):
    return f"""
#!/bin/bash

# Load necessary modules
module load ANSYS/Electromagnetics242

# Activate the Python virtual environment
conda activate pyaedt_11

# Run your Python script
python {path_to_run_file.resolve()} --config config.yaml
    """


def get_bsub_submission_script(execution_dir: Path,
                               simulation_script_path: Path):
    if simulation_script_path.resolve().parent == execution_dir.resolve().parent:
        shorter_simulation_script_path = simulation_script_path.name
    else:
        shorter_simulation_script_path = simulation_script_path.resolve()

    return f"""#!/bin/bash

    # Submit the bsub job to execute hfss_run.sh
    bsub -J hfss_job$project_name \\
        -q short \\
        -oo lsf_output_%J.log \\
        -eo lsf_error_%J.err \\
        -n 6 \\
        -W 08:00 \\
        -R "rusage[mem=50000] span[hosts=1]" \\
        -cwd {execution_dir.resolve()} \\
        {shorter_simulation_script_path}
    """
