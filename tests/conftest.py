# tests/conftest.py
from __future__ import annotations
from pathlib import Path
import sys
import pytest

# ---------------------------------------------------------------------
# Library imports from your package
# ---------------------------------------------------------------------
from pysubmit.workflow import (
    open_pyaedt_file,
    PyaedtFileParameters,
)

# ---------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------
SIMPLE_DESIGN_AEDT = (
    Path(__file__).parent / "resources" / "simple_design.aedt"
)  # spelling kept from the prompt :)




@pytest.fixture
def fake_build_module(tmp_path, monkeypatch):
    # Create a temporary module named "my_good_module"
    module_name = "my_good_module"
    module_dir = tmp_path / module_name
    module_dir.mkdir()

    # Write an __init__.py with a build() function
    (module_dir / "__init__.py").write_text("""
def build(hfss, design_name, setup_name, name_to_value):
    hfss.set_active_design(design_name)
    for name, value in name_to_value.items():
        hfss[name] = value
        
def build_with_error(hfss):
    raise ValueError("Intentional error in user build")
    
def build_without_hfss():
    pass
""")

    # Add the temporary module path to sys.path
    monkeypatch.syspath_prepend(str(tmp_path))

    # Ensure it's not cached in sys.modules
    sys.modules.pop(module_name, None)

    yield module_name

    # Cleanup: remove from sys.modules after test
    sys.modules.pop(module_name, None)


# ---------------------------------------------------------------------
# 1) open a design and yield an HFSS handle
# ---------------------------------------------------------------------
@pytest.fixture(scope="function")
def simple_design(tmp_path):
    """
    Opens the reference .aedt file **once per test module** and yields the
    HFSS handle.  After all tests in the module run, the context manager
    closes HFSS automatically.
    """
    assert SIMPLE_DESIGN_AEDT.exists(), "Missing test asset: simple_design.aedt"

    # Copy the design into the temp dir so tests never touch the git-tracked file
    local_copy = tmp_path / SIMPLE_DESIGN_AEDT.name
    local_copy.write_bytes(SIMPLE_DESIGN_AEDT.read_bytes())

    params = PyaedtFileParameters(design_name='my_design', file_path=local_copy, non_graphical=True)

    # The helper is a context-manager; use `yield` fixture style
    with open_pyaedt_file(params) as hfss:
        yield hfss


