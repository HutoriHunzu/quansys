import warnings
import typer
from pathlib import Path
from .prepare import prepare_job
from .submit import submit_job
from ..workflow import WorkflowConfig, execute_workflow
from .utils import update_status, read_status

# Suppress FutureWarning from pyaedt
warnings.filterwarnings("ignore", category=FutureWarning, module="pyaedt")

# Create the main Typer app
app = typer.Typer(help="Workflow management commands.")


@app.command()
def submit(
        config_path: Path = typer.Argument(..., help="Path to the config.yaml file."),
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
    if project_dir.exists() and not overwrite:
        typer.echo(f"Project '{name}' already exists. Use --overwrite to replace it.")
        raise typer.Exit()

    # Remove the existing project folder if overwrite is enabled
    if project_dir.exists() and overwrite:
        typer.echo(f"Overwriting the existing project '{name}'...")
        import shutil
        shutil.rmtree(project_dir)

    # Load and validate config.yaml
    config = WorkflowConfig.load_from_yaml(config_path)

    # Prepare the job
    results_dir = prepare_job(config, files, mem, timeout)

    # Set status to "pending"
    update_status(project_dir, "pending")

    if prepare:
        typer.echo(f"Job prepared. Results directory: {results_dir}")
    else:
        # Submit the job
        submit_job(results_dir)
        update_status(project_dir, "pending")
        typer.echo(f"Job submitted. Results directory: {results_dir}")


@app.command()
def rerun(
        project_dir: Path = typer.Argument(..., help="Path to the project folder."),
):
    """
    Rerun a job from an existing project directory.
    """
    # Check if the project directory exists
    if not project_dir.exists():
        typer.echo(f"Project directory '{project_dir}' does not exist.")
        raise typer.Exit()

    # Read the status file
    status = read_status(project_dir)

    if status == "running":
        typer.echo(f"Job in project '{project_dir.name}' is already running.")
        raise typer.Exit()
    elif status == "done":
        typer.confirm(
            f"Job in project '{project_dir.name}' is marked as 'done'. Do you want to rerun it?",
            abort=True,
        )
    elif status == "failed":
        typer.echo(f"Re-running failed job in project '{project_dir.name}'...")
    else:
        typer.echo(f"Unknown status '{status}' in '{project_dir}/STATUS.txt'.")
        raise typer.Exit()

    # Re-submit the job
    submit_job(project_dir)
    update_status(project_dir, "running")


@app.command()
def run_flow(config_path: Path = typer.Argument(..., help="Path to the config.yaml file.")):
    """
    Load the config.yaml and execute the workflow.
    Updates the status file upon success or failure.
    """
    # Load config.yaml
    config = WorkflowConfig.load_from_yaml(config_path)
    project_dir = config_path.parent

    # Check the current status
    current_status = read_status(project_dir)
    if current_status != "pending":
        typer.echo(f"Cannot start execution. Current status is '{current_status}', not 'pending'.")
        raise typer.Exit()

    # Update status to "running" before starting
    update_status(project_dir, "running")

    try:
        # Execute the flow
        execute_workflow(config)
        typer.echo(f"Flow execution completed for config: {config_path}")
        # Update status to "done" upon success
        update_status(project_dir, "done")
    except Exception as e:
        # Log the error and update status to "failed"
        typer.echo(f"Flow execution failed: {e}")
        update_status(project_dir, "failed")
        raise e  # Optionally re-raise the exception for debugging


if __name__ == "__main__":
    app()
