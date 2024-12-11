from ansys.aedt.core import Hfss


def run(project_name,
        design_name,
        version='2024.2',
        config=None):
    # use config to infer setup configuration

    # Loading HFSS
    hfss = Hfss(version=version,
                new_desktop=False,
                design=design_name,
                project=project_name,
                non_graphical=True)

    # Checking loading was successful

    # Analyze
    hfss.analyze(gpus=3072, cores=8)

    # Save and exit
    hfss.save_project()
    hfss.release_desktop()
