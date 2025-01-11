from contextlib import contextmanager
from .config import SessionParameters
from ansys.aedt.core.desktop import Desktop
from ansys.aedt.core.hfss import Hfss


@contextmanager
def start_hfss_session(session_parameters: SessionParameters) -> Hfss:
    with Desktop(non_graphical=session_parameters.non_graphical,
                 version=session_parameters.version,
                 new_desktop=session_parameters.new_desktop,
                 close_on_exit=session_parameters.close_on_exit) as session:

        hfss = Hfss(design='temp', project=str(session_parameters.file_path.resolve()))

        try:
            # Yield the HFSS instance to the context
            yield hfss

        finally:
            # Code here runs after the `with` block, before Desktop.__exit__
            print("Cleaning up: Deleting temporary HFSS design.")
            hfss.delete_design("temp")
