class LicenseUnavailableError(Exception):
    """Raised when AEDT license isn't available."""

from contextlib import contextmanager
from typing import Generator
from pathlib import Path
from ansys.aedt.core.hfss import Hfss
from .config import PyaedtFileParameters





