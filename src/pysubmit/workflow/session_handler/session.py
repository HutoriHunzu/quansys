from contextlib import contextmanager
from .config import PyaedtFileParameters
from ansys.aedt.core.hfss import Hfss
from typing import Generator


# @contextmanager
# def open_pyaedt_file(parameters: PyaedtFileParameters) -> Generator[Hfss, None, None]:
#     with Hfss(non_graphical=parameters.non_graphical,
#               version=parameters.version,
#               new_desktop=parameters.new_desktop,
#               close_on_exit=parameters.close_on_exit,
#               design=parameters.design_name,
#               project=str(parameters.file_path.resolve()),
#               remove_lock=True) as hfss:
#
#         try:
#             # Yield the HFSS instance to the context
#             yield hfss
#
#         finally:
#             # Code here runs after the `with` block, before Desktop.__exit__
#             if 'temp' in hfss.design_list:
#                 print("Cleaning up: Deleting temporary HFSS design.")
#                 hfss.delete_design("temp")


from contextlib import contextmanager
import re
from typing import Generator
from ansys.aedt.core.hfss import Hfss
from .config import PyaedtFileParameters

class LicenseUnavailableError(Exception):
    """Raised when AEDT license isn't available."""

from contextlib import contextmanager
from typing import Generator
from pathlib import Path
from ansys.aedt.core.hfss import Hfss
from .config import PyaedtFileParameters



@contextmanager
def open_pyaedt_file(parameters: PyaedtFileParameters) -> Generator[Hfss, None, None]:
    with Hfss(
        non_graphical=parameters.non_graphical,
        version=parameters.version,
        new_desktop=parameters.new_desktop,
        close_on_exit=parameters.close_on_exit,
        design=parameters.design_name,
        project=str(parameters.file_path.resolve()),
        remove_lock=True
    ) as hfss:
        # Immediately check if HFSS initialized to a valid state
        if not hfss.valid_design:
            # Close the session and signal unavailability
            raise LicenseUnavailableError(
                "HFSS session created but no valid design — likely license or startup issue."
            )

        try:
            yield hfss
        finally:
            # Optional cleanup
            if 'temp' in hfss.design_list:
                print("Cleaning up: Deleting temporary HFSS design.")
                hfss.delete_design("temp")

