from ansys.aedt.core import Hfss

from ..config_handler import ConfigProject


def hfss_open(config: ConfigProject) -> Hfss:


    # Loading HFSS
    hfss = Hfss(version=config.version,
                new_desktop=False,
                design=config.design_name,
                project=config.project_name,
                non_graphical=True)

    return hfss
