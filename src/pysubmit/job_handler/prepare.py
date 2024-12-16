from pathlib import Path
import shutil
import subprocess
from .submission_template import (get_simulation_script,
                                  get_bsub_submission_script,
                                  write_sh_file)

from ..simulation.config_handler import Config, load, save, ConfigProject


def prepare_dir(aedt_file_path: Path,
                config: Config,
                dir_path: Path):
    # set the stage for execution of bsub command
    # should do the following

    # create dir
    dir_path.mkdir()

    # copy aedt file
    dst_aedt_path = dir_path / aedt_file_path.name
    shutil.copy(aedt_file_path, dst_aedt_path)

    # changing the config project_path
    config.config_project.original_path = str(aedt_file_path.resolve())
    config.config_project.path = str(dst_aedt_path.name)

    # save new config
    save(dir_path / 'config.yaml', config)

    # create a submission file (submit.sh)
    path_to_run_file = Path('')
    simulation_path = prepare_simulation_script(dir_path, path_to_run_file)
    prepare_job_submission_script(dir_path, simulation_path, config.config_project)

    # update status
    pass


def prepare_simulation_script(dir_path: Path, path_to_run_file: Path):
    txt = get_simulation_script(path_to_run_file)
    simulation_path = write_sh_file(dir_path / 'simulation_script.sh', txt)
    return simulation_path


def prepare_job_submission_script(dir_path: Path, simulation_path: Path, config_project: ConfigProject):
    txt = get_bsub_submission_script(dir_path, simulation_path, config_project)
    job_submission_path = write_sh_file(dir_path / 'job_submission_script.sh', txt)
    return job_submission_path
