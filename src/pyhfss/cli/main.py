import warnings
import typer
from pathlib import Path
import shutil
from .prepare import prepare_job
from .submit import submit_job
from .run import run_job


# Suppress FutureWarning from pyaedt
warnings.filterwarnings("ignore", category=FutureWarning, module="pyaedt")

# Create the main Typer app
app = typer.Typer(help="Workflow management commands.")


@app.command()
def submit(
        config_path: Path = typer.Argument(..., help="Path to the config.yaml file."),
        venv: str = typer.Argument(..., help="Name of the conda virtual environment to be activated"),
        name: str = typer.Option(..., "--name", "-n", help="Project name for the workflow."),
        files: list[Path] = typer.Option(None, "--files", "-f", help="Additional files to copy."),
        mem: int = typer.Option(120000, "--mem", "-m", help="Total memory required in MB."),
        timeout: str = typer.Option("03:00", "--timeout", "-t", help="Job duration in HH:MM format."),
        prepare: bool = typer.Option(False, "--prepare", "-p", help="Only prepare the job without submitting."),
        overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite the existing project folder."),
):
    """
    Prepare and optionally submit a simulation workflow to the cluster.
    """
    # Define project directory
    project_dir = Path(name)

    # Check if the project directory exists
    # if project_dir.exists() and not overwrite:
    #     typer.echo(f"Project '{name}' already exists. Use --overwrite to replace it.")
    #     raise typer.Exit()

    # Remove the existing project folder if overwrite is enabled
    if project_dir.exists() and overwrite:
        typer.echo(f"Overwriting the existing project '{name}'...")
        shutil.rmtree(project_dir)

    # Prepare the job
    results_dir = prepare_job(config_path, project_dir, files, mem, timeout, venv)

    if prepare:
        typer.echo(f"Job prepared. Results directory: {results_dir}")

    else:
        # Submit the job
        submit_job(results_dir)
        typer.echo(f"Job submitted. Results directory: {results_dir}")




@app.command()
def run(config_path: Path = typer.Argument(..., help="Path to the config.yaml file.")):
    """
    Load the config.yaml and execute the workflow.
    Updates the status file upon success or failure.
    """
    # Load config.yaml
    try:
        # Execute the flow
        run_job(config_path)
        typer.echo(f"Flow execution completed for config: {config_path}")
    except Exception as e:
        # Log the error and update status to "failed"
        typer.echo(f"Flow execution failed: {e}")
        raise e  # Optionally re-raise the exception for debugging


if __name__ == "__main__":
    app()
