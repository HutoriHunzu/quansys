from pathlib import Path
import subprocess
from ..simulation.config_handler import ConfigProject


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

# sourceing conda
source /apps/easybd/programs/miniconda/24.9.2_environmentally/etc/profile.d/conda.sh

# loading conda
module load miniconda/24.9.2_environmentally

# Activate the Python virtual environment
conda activate pyaedt_11

# Run your Python script
submit-run --config config.yaml
    """


def get_bsub_submission_script(execution_dir: Path,
                               simulation_script_path: Path,
                               config_project: ConfigProject):
    if simulation_script_path.resolve().parent == execution_dir.resolve().parent:
        shorter_simulation_script_path = simulation_script_path.name
    else:
        shorter_simulation_script_path = simulation_script_path.resolve()

    gpus = config_project.gpus
    if gpus == 1:
        gpu_string = '\n-gpu num=1:j_exclusive=yes:gmem=8G:gmodel=NVIDIAA40 \\'
        queue = 'short-gpu'
    else:
        gpu_string = ''
        queue = 'short'

    return f"""#!/bin/bash
    
    # Submit the bsub job to execute hfss_run.sh
    bsub -J hfss_job$project_name \\
        -q {queue} \\
        -oo lsf_output_%J.log \\
        -eo lsf_error_%J.err \\
        -n {config_project.cores} \\
        -W 02:00 \\
        -R "rusage[mem=20000] span[hosts=1]" \\{gpu_string}
        -cwd {execution_dir.resolve()} \\
        {shorter_simulation_script_path}
    """

#     f"""
#     REMOTE_TMP_DIR=${TMPDIR:-/tmp}/hfss_${USER}_$$
#     RESULTS_DIR="{execution_dir.resolve()}/results"
#
#     # Create results directory locally if not already present
#     mkdir -p "$RESULTS_DIR"
#
#     # Copy necessary files to the remote node's temporary directory
#     bsub -J hfss_job$project_name \
#         -q {queue} \
#         -oo lsf_output_%J.log \
#         -eo lsf_error_%J.err \
#         -n {config_project.cores} \
#         -W 02:00 \
#         -R "rusage[mem=20000] span[hosts=1]" \\{gpu_string} \
#         -cwd "$RESULTS_DIR" \
#         <<EOF
#
#     #!/bin/bash
#
#     # Create temporary directory on the remote node
#     mkdir -p "$REMOTE_TMP_DIR"
#
#     # Copy project files to the remote temporary directory
#     cp {execution_dir.resolve()}/* "$REMOTE_TMP_DIR"
#
#     # Load the HFSS module/environment if necessary
#     module load hfss
#
#     # Run HFSS
#     cd "$REMOTE_TMP_DIR"
#     hfss -batchsolve -ng -monitor -input my_project.aedt
#
#     # Copy results back to the execution directory
#     cp "$REMOTE_TMP_DIR"/* "$RESULTS_DIR"
#
#     # Clean up the temporary directory
#     rm -rf "$REMOTE_TMP_DIR"
#
#     EOF
#
#
# """
