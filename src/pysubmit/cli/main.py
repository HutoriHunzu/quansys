import typer
from pathlib import Path
from .prepare import prepare_job
from .submit import submit_job
from ..workflow import WorkflowConfig

app = typer.Typer()


@app.command()
def submit(
        config_path: Path = typer.Argument(..., help="Path to the config.yaml file."),
        name: str = typer.Option(None, "--name", "-n", help="Override the project name."),
        files: list[Path] = typer.Option(None, "--files", "-f", help="Additional files to copy."),
        mem: int = typer.Option(120, "--mem", "-m", help="Total memory required in GB."),
        prepare: bool = typer.Option(False, "--prepare", "-p", help="Only prepare the job without submitting."),
):
    """
    Prepare and optionally submit a simulation workflow to the cluster.
    """
    # Load and validate config.yaml
    config = WorkflowConfig.load_from_yaml(config_path)

    # Override project name if provided
    if name:
        config.data_parameters.project_name = name

    # Prepare the job
    results_dir = prepare_job(config, files, mem)

    if prepare:
        typer.echo(f"Job prepared. Results directory: {results_dir}")
    else:
        # Submit the job
        submit_job(results_dir)
        typer.echo(f"Job submitted. Results directory: {results_dir}")


if __name__ == "__main__":
    app()
