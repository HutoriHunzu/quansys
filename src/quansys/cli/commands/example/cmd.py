"""
Example command - lightweight signature only, heavy logic in impl.py
"""
import typer

def example(
    example_type: str = typer.Option(
        "simple",
        "--type",
        "-t",
        help="Type of example files to copy ('simple' or 'complex')",
        show_default=True
    ),
    with_config: bool = typer.Option(True, "--with-config/--no-config", help="Include config file in output"),
    example_list: bool = typer.Option(False, "--list", help="Show available example types and exit")
):
    """
    Copy example AEDT and optionally config files to the current directory.
    """
    # Handle --list immediately without any heavy imports
    if example_list:
        typer.echo("Available example types:")
        typer.echo("  - simple   : resonator on silicon chip (eigenmode analysis)")
        typer.echo("  - complex  : transmon + resonator coupled system (quantum EPR)")
        raise typer.Exit()

    # Lazy import the heavy implementation only when actually copying files
    from .impl import execute_example
    
    return execute_example(
        example_type=example_type,
        with_config=with_config
    )