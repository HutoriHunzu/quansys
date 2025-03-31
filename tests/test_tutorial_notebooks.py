import pytest

# Define the paths to your notebooks
notebook_paths = [
    "./tutorial/01_simulations.ipynb",
    "./tutorial/02_quantum_epr.ipynb",
    "./tutorial/03_builder.ipynb",
    "./tutorial/04_sweeper.ipynb",
    "./tutorial/05_data_handler.ipynb",
    "./tutorial/06_workflow.ipynb"
]

@pytest.mark.parametrize("notebook_path", notebook_paths)
def test_notebook_execution(notebook_path):
    pytest.main(["--nbmake", notebook_path])
