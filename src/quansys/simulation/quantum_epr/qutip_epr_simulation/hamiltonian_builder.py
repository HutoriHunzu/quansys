
"""
Quantum Hamiltonian construction for EPR analysis.
"""

import numpy as np
import qutip

from .constants import reduced_flux_quantum, Planck
from .matrix_operations import cosine_taylor_series
from .composite_space import CompositeSpace



def build_quantum_hamiltonian(
        cspace: CompositeSpace,
        frequencies_hz: np.ndarray,
        inductances_h: np.ndarray,
        junction_flux_zpfs: np.ndarray,
        cosine_truncation: int = 5
    ) -> qutip.Qobj:
    """
    Build the quantum Hamiltonian for EPR analysis.
    
    Constructs H = H_linear + H_nonlinear where H_linear contains harmonic oscillator 
    terms and H_nonlinear contains cosine junction interactions from the Josephson 
    junction energy E_J * cos(phi/phi_0).
    """
    n_modes = len(frequencies_hz)
    n_junctions = len(inductances_h)

    zpfs = np.transpose(np.array(junction_flux_zpfs))  # Ensure J x N shape

    junction_energies_j = reduced_flux_quantum ** 2 / inductances_h
    junction_frequencies_hz = junction_energies_j / Planck

    _validate_hamiltonian_inputs(frequencies_hz, inductances_h, zpfs, n_modes, n_junctions)

    # Build Hamiltonian parts
    linear_part = _create_linear_part(cspace, frequencies_hz)
    nonlinear_part = _build_nonlinear_hamiltonian(zpfs, cspace, junction_frequencies_hz, cosine_truncation)

    return linear_part + nonlinear_part



def _create_linear_part(cspace: CompositeSpace, frequencies_hz: np.ndarray) -> qutip.Qobj:
    """Create linear Hamiltonian part: sum(omega_i * n_i)."""
    ops = []
    for space, frequency_hz in zip(cspace.spaces_ordered, frequencies_hz):
        op = frequency_hz * cspace.expand_operator(space.name, space.num_op())
        ops.append(op)

    return np.sum(ops)


def _build_nonlinear_hamiltonian(zpfs: np.ndarray,
                                 cspace: CompositeSpace,
                                 junction_frequencies_hz: np.ndarray,
                                 cosine_truncation: int) -> qutip.Qobj:
    """Build the nonlinear part of the Hamiltonian from cosine junction terms."""

    assert(len(zpfs) == len(junction_frequencies_hz))

    ops = []

    field_operators = [cspace.expand_operator(space.name, space.field_op())
                       for space in cspace.spaces_ordered]

    for zpf, junction_frequency_hz in zip(zpfs, junction_frequencies_hz):

        cosine_arg = np.dot(zpf / reduced_flux_quantum, field_operators)
        cosine_op = cosine_taylor_series(cosine_arg, cosine_truncation)

        op = cosine_op * (-1) * junction_frequency_hz

        ops.append(op)

    return np.sum(ops)




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
