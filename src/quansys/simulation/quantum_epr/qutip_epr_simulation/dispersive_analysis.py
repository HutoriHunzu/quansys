"""
Dispersive analysis for extracting dressed frequencies and cross-Kerr interactions.
"""

from typing import Union, Optional
import numpy as np
import qutip


def extract_dispersive_parameters(hamiltonian: Union[qutip.Qobj, list[qutip.Qobj]], 
                                fock_truncation: int,
                                zero_point_fluctuations: Optional[np.ndarray] = None, 
                                linear_frequencies: Optional[np.ndarray] = None) -> tuple[np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Extract dressed mode frequencies and chi matrix from Hamiltonian eigenanalysis.
    
    Diagonalizes the Hamiltonian and assigns quantum numbers to eigenstates based on
    maximum overlap with bare Fock states. Then extracts dressed frequencies and
    cross-Kerr matrix elements.
    """
    full_hamiltonian = _prepare_hamiltonian(hamiltonian)
    eigenvalues, eigenvectors = _diagonalize_hamiltonian(full_hamiltonian)
    
    n_modes = _calculate_number_of_modes(full_hamiltonian, fock_truncation)
    
    dressed_frequencies = _extract_dressed_frequencies(
        eigenvalues, eigenvectors, n_modes, fock_truncation
    )
    
    chi_matrix = _calculate_chi_matrix(
        eigenvalues, eigenvectors, dressed_frequencies, n_modes, fock_truncation
    )
    
    return dressed_frequencies, chi_matrix, zero_point_fluctuations, linear_frequencies


def _prepare_hamiltonian(hamiltonian: Union[qutip.Qobj, list[qutip.Qobj]]) -> qutip.Qobj:
    """Convert hamiltonian input to single Qobj."""
    if isinstance(hamiltonian, list):
        if len(hamiltonian) != 2:
            raise ValueError("Hamiltonian list must contain exactly [linear, nonlinear] parts")
        linear_ham, nonlinear_ham = hamiltonian
        return linear_ham + nonlinear_ham
    elif isinstance(hamiltonian, qutip.Qobj):
        return hamiltonian
    else:
        raise ValueError("Hamiltonian must be a qutip.Qobj or list of [linear, nonlinear] Qobjs")


def _diagonalize_hamiltonian(hamiltonian: qutip.Qobj) -> tuple[np.ndarray, list[qutip.Qobj]]:
    """Diagonalize Hamiltonian and return eigenvalues/eigenvectors."""
    eigenvalues, eigenvectors = hamiltonian.eigenstates()
    # Shift energies relative to ground state
    eigenvalues = eigenvalues - eigenvalues[0]
    return eigenvalues, eigenvectors


def _calculate_number_of_modes(hamiltonian: qutip.Qobj, fock_truncation: int) -> int:
    """Determine number of modes from Hamiltonian dimension."""
    hamiltonian_dimension = hamiltonian.shape[0]
    n_modes = int(np.log(hamiltonian_dimension) / np.log(fock_truncation))
    
    if hamiltonian_dimension != fock_truncation ** n_modes:
        raise ValueError(f"Hamiltonian dimension {hamiltonian_dimension} "
                        f"inconsistent with fock_truncation={fock_truncation}")
    
    return n_modes


def _create_fock_state(excitation_numbers: dict[int, int], n_modes: int, fock_truncation: int) -> qutip.Qobj:
    """Create Fock state |n0, n1, n2, ...> from excitation dictionary."""
    return qutip.tensor(*[qutip.basis(fock_truncation, excitation_numbers.get(i, 0)) 
                         for i in range(n_modes)])


def _find_closest_eigenstate(target_state: qutip.Qobj, eigenvalues: np.ndarray, 
                           eigenvectors: list[qutip.Qobj]) -> tuple[float, qutip.Qobj]:
    """Find eigenstate with maximum overlap with target Fock state."""
    overlaps = [np.abs(target_state.dag() * eigenvector) for eigenvector in eigenvectors]
    max_overlap_index = np.argmax(overlaps)
    return eigenvalues[max_overlap_index], eigenvectors[max_overlap_index]


def _extract_dressed_frequencies(eigenvalues: np.ndarray, eigenvectors: list[qutip.Qobj],
                               n_modes: int, fock_truncation: int) -> np.ndarray:
    """Extract single-excitation frequencies (dressed frequencies)."""
    dressed_frequencies = []
    
    for mode_idx in range(n_modes):
        single_excitation_state = _create_fock_state({mode_idx: 1}, n_modes, fock_truncation)
        dressed_energy, _ = _find_closest_eigenstate(single_excitation_state, eigenvalues, eigenvectors)
        dressed_frequencies.append(dressed_energy)
    
    return np.array(dressed_frequencies)


def _calculate_chi_matrix(eigenvalues: np.ndarray, eigenvectors: list[qutip.Qobj],
                        dressed_frequencies: np.ndarray, n_modes: int, fock_truncation: int) -> np.ndarray:
    """Calculate chi matrix (cross-Kerr interactions)."""
    chi_matrix = np.zeros((n_modes, n_modes))
    
    for i in range(n_modes):
        for j in range(i, n_modes):
            # Create state with one excitation in mode i and one in mode j
            excitation_state = _create_fock_state({i: 1, j: 1}, n_modes, fock_truncation)
            two_excitation_energy, _ = _find_closest_eigenstate(excitation_state, eigenvalues, eigenvectors)
            
            # Chi is the deviation from linear sum of single-excitation energies
            chi_ij = two_excitation_energy - (dressed_frequencies[i] + dressed_frequencies[j])
            chi_matrix[i, j] = chi_ij
            chi_matrix[j, i] = chi_ij  # Symmetric matrix
    
    return chi_matrix