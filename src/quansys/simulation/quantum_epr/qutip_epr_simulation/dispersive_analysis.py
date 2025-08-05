"""
Dispersive analysis for extracting dressed frequencies and cross-Kerr interactions.
"""

import numpy as np
from numpy.typing import NDArray
import qutip
from itertools import combinations_with_replacement
from .composite_space import CompositeSpace


MINIMAL_IMAG_INACCURACY = 1e-10  # Minimum imaginary part to consider as non-zero


def extract_dispersive_parameters(
        cspace: CompositeSpace,
        hamiltonian: qutip.Qobj,
        fock_truncation: int,
        zero_point_fluctuations: np.ndarray | None = None,
        linear_frequencies: np.ndarray | None = None) -> tuple[
    np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None]:
    """
    Extract dressed mode frequencies and chi matrix from Hamiltonian eigenanalysis.
    
    Diagonalizes the Hamiltonian and assigns quantum numbers to eigenstates based on
    maximum overlap with bare Fock states. Then extracts dressed frequencies and
    cross-Kerr matrix elements.
    """
    eigenvalues, eigenvectors = _diagonalize_hamiltonian(hamiltonian)

    dressed_frequencies = _extract_dressed_frequencies(
        cspace,
        eigenvalues, eigenvectors
    )

    chi_matrix = _calculate_chi_matrix(
        cspace,
        eigenvalues, eigenvectors, dressed_frequencies
    )

    return dressed_frequencies, chi_matrix, zero_point_fluctuations, linear_frequencies


def _diagonalize_hamiltonian(hamiltonian: qutip.Qobj) -> tuple[np.ndarray, list[qutip.Qobj]]:
    """Diagonalize Hamiltonian and return eigenvalues/eigenvectors."""
    eigenvalues, eigenvectors = hamiltonian.eigenstates()
    # Shift energies relative to ground state
    eigenvalues = eigenvalues - eigenvalues[0]
    # Check real energies
    if np.any(np.imag(eigenvalues) > MINIMAL_IMAG_INACCURACY):
        raise ValueError("Hamiltonian eigenvalues have non-zero imaginary part.")
    eigenvalues = np.real(eigenvalues).astype(float)

    return eigenvalues, eigenvectors


def _create_fock_state(cspace: CompositeSpace, excitation_numbers: dict[int, int]) -> qutip.Qobj:
    """Create Fock state |n0, n1, n2, ...> from excitation dictionary."""
    name_op_dict = {space.name: space.basis(excitation_numbers.get(space.name))
                    for space in cspace.spaces_ordered}
    return cspace.tensor(name_op_dict)


def _find_closest_eigenstate(target_state: qutip.Qobj, eigenvalues: NDArray[float],
                             eigenvectors: list[qutip.Qobj]) -> tuple[float, qutip.Qobj]:
    """Find eigenstate with maximum overlap with target Fock state."""
    overlaps = [np.abs(target_state.overlap(eigenvector)) for eigenvector in eigenvectors]
    max_overlap_index = np.argmax(overlaps)
    return float(eigenvalues[max_overlap_index]), eigenvectors[max_overlap_index]


def _extract_dressed_frequencies(cspace: CompositeSpace, eigenvalues: np.ndarray, eigenvectors: list[qutip.Qobj]) -> np.ndarray:
    """Extract single-excitation frequencies (dressed frequencies)."""
    n_modes = len(cspace.spaces_ordered)
    dressed_frequencies = []

    for mode_idx in range(n_modes):
        single_excitation_state = _create_fock_state(cspace, {mode_idx: 1})
        dressed_energy, _ = _find_closest_eigenstate(single_excitation_state, eigenvalues, eigenvectors)
        dressed_frequencies.append(dressed_energy)

    return np.array(dressed_frequencies)


def _calculate_chi_matrix(cspace: CompositeSpace, eigenvalues: np.ndarray, eigenvectors: list[qutip.Qobj],
                          dressed_frequencies: np.ndarray) -> np.ndarray:
    """Calculate chi matrix (cross-Kerr interactions)."""
    n_modes = len(cspace.spaces_ordered)
    chi_matrix = np.zeros((n_modes, n_modes))

    for i, j in combinations_with_replacement(range(n_modes), 2):
        # Create state with one excitation in mode i and one in mode j
        excitation_number = dict(enumerate([0] * n_modes))
        excitation_number[i] += 1
        excitation_number[j] += 1

        excitation_state = _create_fock_state(cspace, excitation_number)
        two_excitation_energy, _ = _find_closest_eigenstate(
            excitation_state, eigenvalues, eigenvectors
        )

        # Chi is the deviation from linear sum of single-excitation energies
        single_excitation_energy = dressed_frequencies[i] + dressed_frequencies[j]
        chi_ij = two_excitation_energy - single_excitation_energy

        # Check no imaginary part
        if np.imag(chi_ij) > MINIMAL_IMAG_INACCURACY:
            raise ValueError(f"Chi matrix element {i}, {j} has non-zero imaginary part: {chi_ij}")
        chi_ij = np.real(chi_ij)

        chi_matrix[i, j] = chi_ij
        chi_matrix[j, i] = chi_ij  # Symmetric matrix

    return chi_matrix
