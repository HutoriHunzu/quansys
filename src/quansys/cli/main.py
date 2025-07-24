import warnings
import typer

# Import lightweight command signatures - no heavy imports here!
from .commands.submit import submit
from .commands.run import run
from .commands.example import example

# Suppress FutureWarning from pyaedt
warnings.filterwarnings("ignore", category=FutureWarning, module="pyaedt")

# Create the main Typer app - keep rich features for nice CLI experience
app = typer.Typer(help="Workflow management commands.")

# Register commands with typer - this allows proper introspection
app.command()(submit)
app.command()(run)
app.command()(example)

if __name__ == "__main__":
    app()
