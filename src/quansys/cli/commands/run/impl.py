"""
Run command implementation - contains all heavy imports and logic
"""

import typer


def execute_run(config_path):
    """
    Main run implementation - all heavy logic happens here.
    This function is only imported when the run command is actually called.
    """
    try:
        import quansys.workflow as workflow
        # from quansys.workflow import WorkflowConfig, execute_workflow

        # Execute the workflow
        config = workflow.WorkflowConfig.load_from_yaml(config_path)
        workflow.execute_workflow(config)

        typer.echo(f"Flow execution completed for config: {config_path}")

    except Exception as e:
        # Log the error and update status to "failed"
        typer.echo(f"Flow execution failed: {e}")
        raise e  # Optionally re-raise the exception for debugging
