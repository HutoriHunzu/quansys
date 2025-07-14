from pydantic import BaseModel
from pathlib import Path
from typing_extensions import Annotated, Literal
from pydantic import BeforeValidator

from ansys.aedt.core.hfss import Hfss

from contextlib import contextmanager
from typing import Generator


def ensure_path(value: Path | str) -> Path:
    if isinstance(value, str):
        return Path(value)
    else:
        return value


PATH_TYPE = Annotated[Path, BeforeValidator(ensure_path)]

class LicenseUnavailableError(Exception):
    """Raised when AEDT license isn't available."""


class PyaedtFileParameters(BaseModel):
    """
    Configuration for launching and managing an AEDT (HFSS) session.

    This object controls how the `.aedt` file is opened, including settings
    related to license availability, GUI behavior, and session cleanup.

    It is used during the *prepare*, *build*, and *simulate* phases
    of the simulation workflow.

    Attributes:
        file_path: Path to the source `.aedt` project file.
        design_name: Name of the design to open (defaults to "temp").
        version: AEDT version to use (e.g., "2024.2").
        non_graphical: Whether to run AEDT in non-graphical mode.
        new_desktop: If True, starts a new AEDT desktop instance.
        close_on_exit: Whether to automatically close AEDT after exiting the context.
    """

    file_path: PATH_TYPE
    design_name: str = 'temp'
    version: Literal['2024.2'] = '2024.2'
    non_graphical: bool = True
    new_desktop: bool = True
    close_on_exit: bool = True

    @contextmanager
    def open_pyaedt_file(self) -> Generator[Hfss, None, None]:
        """
        Open an HFSS session using the specified file and settings.

        Returns a context-managed `Hfss` instance that is ready to use.

        Yields:
            An active and validated `Hfss` object.

        Raises:
            LicenseUnavailableError: If no valid design is loaded (e.g., license issue).
        """
        with Hfss(
                non_graphical=self.non_graphical,
                version=self.version,
                new_desktop=self.new_desktop,
                close_on_exit=self.close_on_exit,
                design=self.design_name,
                project=str(self.file_path.resolve()),
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
                hfss.save_project()
            finally:
                # Optional cleanup
                if 'temp' in hfss.design_list:
                    print("Cleaning up: Deleting temporary HFSS design.")
                    hfss.delete_design("temp")
