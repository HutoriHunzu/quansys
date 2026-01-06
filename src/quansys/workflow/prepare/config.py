from pydantic import BaseModel


class PrepareFolderConfig(BaseModel):
    """
    Configuration for the *prepare* phase of the workflow.

    This determines how the working directory is initialized
    before the simulation is executed.

    Attributes:
        copy_enabled: If True, the source AEDT file will be copied; otherwise, it runs in-place.
        dest_name: Filename to use for the copied AEDT file inside each simulation folder.
    """

    copy_enabled: bool = True  # switch off to run in-place
    dest_name: str = "build.aedt"  # file name inside each run folder
