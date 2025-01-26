import shutil
from datetime import datetime
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
