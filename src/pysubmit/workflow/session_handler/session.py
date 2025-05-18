from contextlib import contextmanager
from .config import SessionParameters
from ansys.aedt.core.hfss import Hfss
from typing import Generator


@contextmanager
def start_hfss_session(session_parameters: SessionParameters) -> Generator[Hfss, None, None]:
    with Hfss(non_graphical=session_parameters.non_graphical,
              version=session_parameters.version,
              new_desktop=session_parameters.new_desktop,
              close_on_exit=session_parameters.close_on_exit,
              design=session_parameters.design_name,
              project=str(session_parameters.file_path.resolve()),
              remove_lock=True) as hfss:

        try:
            # Yield the HFSS instance to the context
            yield hfss

        finally:
            # Code here runs after the `with` block, before Desktop.__exit__            
            if 'temp' in hfss.design_list:
                print("Cleaning up: Deleting temporary HFSS design.")
                hfss.delete_design("temp")
