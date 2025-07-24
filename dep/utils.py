from datetime import datetime
import shutil
from pathlib import Path

def generate_timestamp():
    """
    Generate a timestamp for directory naming.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def copy_files(files, target_dir):
    """
    Copy a list of files to the target directory.
    """
    for file in files:
        if not Path(file).exists():
            raise FileNotFoundError(f"File not found: {file}")
        shutil.copy(file, target_dir)



def update_status(project_dir: Path, status: str):
    """
    Update the STATUS.txt file in the project directory.
    """
    status_file = project_dir / "STATUS.txt"
    status_file.write_text(status)


def read_status(project_dir: Path) -> str:
    """
    Read the status from the STATUS.txt file.
    """
    status_file = project_dir / "STATUS.txt"
    if not status_file.exists():
        return "unknown"
    return status_file.read_text().strip()
