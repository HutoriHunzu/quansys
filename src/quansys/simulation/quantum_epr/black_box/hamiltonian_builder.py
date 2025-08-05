"""
Quantum Hamiltonian construction for EPR analysis.
"""

from functools import reduce
from typing import Union
import numpy as np
import qutip

from .constants import Planck as h, reduced_flux_quantum
from .matrix_operations import dot_product, cosine_taylor_series


def build_quantum_hamiltonian(mode_frequencies_hz: np.ndarray, 
                            junction_inductances_h: np.ndarray,
                            junction_flux_zpfs: np.ndarray, 
                            cosine_truncation: int = 5, 
                            fock_truncation: int = 8, 
                            return_separate_parts: bool = False) -> Union[qutip.Qobj, tuple[qutip.Qobj, qutip.Qobj]]:
    """
    Build the quantum Hamiltonian for EPR analysis.
    
    Takes linear mode frequencies and zero-point fluctuations to construct
    the full Hamiltonian matrix assuming cosine junction potential.
    """
    n_modes = len(mode_frequencies_hz)
    n_junctions = len(junction_inductances_h)
    
    frequencies = np.array(mode_frequencies_hz)
    inductances = np.array(junction_inductances_h)
    zpfs = np.transpose(np.array(junction_flux_zpfs))  # Ensure J x N shape
    
    junction_energies_j = reduced_flux_quantum**2 / inductances
    junction_frequencies_hz = junction_energies_j / h
    
    _validate_hamiltonian_inputs(frequencies, inductances, zpfs, n_modes, n_junctions)
    
    # Create mode operators
    mode_field_operators = _create_mode_field_operators(n_modes, fock_truncation)
    mode_number_operators = _create_mode_number_operators(n_modes, fock_truncation)
    
    # Build Hamiltonian parts
    linear_part = dot_product(frequencies, mode_number_operators)
    nonlinear_part = _build_nonlinear_hamiltonian(
        zpfs, mode_field_operators, junction_frequencies_hz, cosine_truncation
    )
    
    if return_separate_parts:
        return linear_part, nonlinear_part
    else:
        return linear_part + nonlinear_part


def _create_mode_field_operators(n_modes: int, fock_truncation: int) -> list[qutip.Qobj]:
    """Create field operators (x = a + a†) for all modes."""
    annihilation = qutip.destroy(fock_truncation)
    creation = annihilation.dag()
    field_operator = annihilation + creation
    
    return [_tensor_operator_at_mode(field_operator, mode_idx, n_modes, fock_truncation)
            for mode_idx in range(n_modes)]


def _create_mode_number_operators(n_modes: int, fock_truncation: int) -> list[qutip.Qobj]:
    """Create number operators for all modes."""
    number_operator = qutip.num(fock_truncation)
    
    return [_tensor_operator_at_mode(number_operator, mode_idx, n_modes, fock_truncation)
            for mode_idx in range(n_modes)]


def _tensor_operator_at_mode(operator: qutip.Qobj, mode_index: int, 
                           n_modes: int, fock_truncation: int) -> qutip.Qobj:
    """Create operator tensored with identities at other mode locations."""
    operator_list = [qutip.qeye(fock_truncation) for _ in range(n_modes)]
    operator_list[mode_index] = operator
    return reduce(qutip.tensor, operator_list)


def _build_nonlinear_hamiltonian(zpfs: np.ndarray, mode_field_operators: list[qutip.Qobj],
                                junction_frequencies_hz: np.ndarray, 
                                cosine_truncation: int) -> qutip.Qobj:
    """Build the nonlinear part of the Hamiltonian from cosine junction terms."""
    cosine_arguments = [
        dot_product(zpf_row / reduced_flux_quantum, mode_field_operators) 
        for zpf_row in zpfs
    ]
    
    cosine_terms = [
        cosine_taylor_series(arg, cosine_truncation) 
        for arg in cosine_arguments
    ]
    
    return dot_product(-junction_frequencies_hz, cosine_terms)


def _validate_hamiltonian_inputs(frequencies: np.ndarray, inductances: np.ndarray, 
                               zpfs: np.ndarray, n_modes: int, n_junctions: int):
    """Validate input arrays for Hamiltonian construction."""
    if np.isnan(zpfs).any():
        raise ValueError("Zero-point fluctuations contain NaN values")
    if np.isnan(inductances).any():
        raise ValueError("Junction inductances contain NaN values") 
    if np.isnan(frequencies).any():
        raise ValueError("Mode frequencies contain NaN values")
        
    if zpfs.shape != (n_junctions, n_modes):
        raise ValueError(f"ZPF array shape {zpfs.shape} does not match expected "
                        f"({n_junctions}, {n_modes})")
    if len(frequencies) != n_modes:
        raise ValueError(f"Expected {n_modes} frequencies, got {len(frequencies)}")
    if len(inductances) != n_junctions:
        raise ValueError(f"Expected {n_junctions} inductances, got {len(inductances)}")