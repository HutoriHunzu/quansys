import pytest
from itertools import combinations
from pyhfss.simulation import QuantumEPR

# Constant mapping from mode number to label
MODE_TO_LABEL = {
    1: "transmon",
    2: "readout",
    3: "purcell"
}

# Helper to extract chi values into a flat map for comparison
def extract_chi_map(quantum_result):
    labels = quantum_result.distributed.labels_order
    chi = quantum_result.epr.chi
    return {
        (labels[i], labels[j]): float(chi[i][j].real)
        for i in range(len(labels)) for j in range(len(labels))
    }

# Helper to generate label-to-mode dict from mode numbers
def resolve_modes(mode_numbers):
    return {mode: MODE_TO_LABEL[mode] for mode in mode_numbers}

# Fixture for full 3-mode simulation
@pytest.fixture(scope="module")
def full_epr_result(transmon_readout_purcell_design, transmon_readout_purcell_eigenmode_results):
    sim = QuantumEPR(
        design_name='my_design',
        setup_name='Setup1',
        modes_to_labels=resolve_modes([1, 2, 3]),
        junctions_infos=[
            {'name': 'transmon_junction_line', 'inductance_variable_name': 'junction_inductance'}
        ]
    )
    return sim.analyze(transmon_readout_purcell_design)


# Parametrize just with mode number sets (labels are resolved automatically)
@pytest.mark.parametrize("mode_subset", [
    [1, 2],
    [1, 3],
    [2, 3],
])
def test_epr_submatrix_consistency(transmon_readout_purcell_design, full_epr_result, mode_subset):
    # Run partial simulation
    sim = QuantumEPR(
        design_name='my_design',
        setup_name='Setup1',
        modes_to_labels=resolve_modes(mode_subset),
        junctions_infos=[
            {'name': 'transmon_junction_line', 'inductance_variable_name': 'junction_inductance'}
        ]
    )
    result = sim.analyze(transmon_readout_purcell_design)

    # Extract chi submatrices from both full and partial simulations
    full_chi = extract_chi_map(full_epr_result)
    partial_chi = extract_chi_map(result)

    labels = [MODE_TO_LABEL[m] for m in mode_subset]

    # Compare all relevant combinations: diagonal + upper triangle
    for (i, j) in combinations(range(len(labels)), 2):
        key = (labels[i], labels[j])
        assert key in full_chi and key in partial_chi, f"Missing key {key}"
        assert partial_chi[key] == pytest.approx(full_chi[key], rel=0.15), f"Mismatch for {key}"

    # Also check diagonal entries (anharmonicities)
    for i in range(len(labels)):
        key = (labels[i], labels[i])
        assert key in full_chi and key in partial_chi, f"Missing diagonal {key}"
        assert partial_chi[key] == pytest.approx(full_chi[key], rel=0.15), f"Mismatch for {key}"
