# tests/conftest.py
from __future__ import annotations
from pathlib import Path
import sys
import pytest

# ---------------------------------------------------------------------
# Library imports from your package
# ---------------------------------------------------------------------
from pysubmit.workflow import PyaedtFileParameters
from pysubmit.simulation import EigenmodeAnalysis
from pysubmit.workflow.session_handler.session import LicenseUnavailableError

# ---------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------
SIMPLE_DESIGN_AEDT = (
        Path(__file__).parent / "resources" / "simple_design.aedt"
)

TRANSMON_READOUT_PURCELL_DESIGN_AEDT = (
        Path(__file__).parent / "resources" / "transmon_purcell_readout.aedt"
)


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


@pytest.fixture(scope="module")
def simple_design(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("aedt_project_simple")

    assert SIMPLE_DESIGN_AEDT.exists(), "Missing test asset: simple_design.aedt"

    local_copy = tmp_path / SIMPLE_DESIGN_AEDT.name
    local_copy.write_bytes(SIMPLE_DESIGN_AEDT.read_bytes())

    params = PyaedtFileParameters(
        design_name='my_design',
        file_path=local_copy,
        non_graphical=True
    )

    try:
        with params.open_pyaedt_file() as hfss:
            yield hfss
    except LicenseUnavailableError as e:
        pytest.skip(f"Skipping test: {e}")


@pytest.fixture(scope='module')
def eigenmode_results(simple_design):
    simulation = EigenmodeAnalysis(
        design_name='my_design',
        setup_name='Setup1',
        setup_parameters={
            'NumModes': 5,
            "MaximumPasses": 2,
            "MinimumPasses": 1,
        }
    )

    return simulation.analyze(simple_design)

@pytest.fixture(scope="module")
def transmon_readout_purcell_design(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("aedt_project_complex")

    assert TRANSMON_READOUT_PURCELL_DESIGN_AEDT.exists(), "Missing test asset: transmon_readout_purcell.aedt"

    local_copy = tmp_path / TRANSMON_READOUT_PURCELL_DESIGN_AEDT.name
    local_copy.write_bytes(TRANSMON_READOUT_PURCELL_DESIGN_AEDT.read_bytes())

    params = PyaedtFileParameters(
        design_name='my_design',
        file_path=local_copy,
        non_graphical=True
    )

    try:
        with params.open_pyaedt_file() as hfss:
            yield hfss
    except LicenseUnavailableError as e:
        pytest.skip(f"Skipping test: {e}")


@pytest.fixture(scope="module")
def transmon_readout_purcell_eigenmode_results(transmon_readout_purcell_design):
    simulation = EigenmodeAnalysis(
        design_name='my_design',
        setup_name='Setup1',
        setup_parameters={
            'NumModes': 3,
            "MaximumPasses": 3,
            "MinimumPasses": 1,
        }
    )

    return simulation.analyze(transmon_readout_purcell_design)
