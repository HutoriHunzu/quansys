
"""
Quantum Hamiltonian construction for EPR analysis.
"""

from functools import reduce
import numpy as np
import qutip
from numpy.typing import NDArray

from .constants import Planck as h, reduced_flux_quantum
from .matrix_operations import dot_product, cosine_taylor_series
from .space import Space
from .composite_space import CompositeSpace


def build_quantum_hamiltonian(
        frequencies_hz: NDArray[float],
        inductances_h: NDArray[float],
        junction_flux_zpfs: NDArray[float],
        cosine_truncation: int = 5,
        fock_truncation: int = 8,
        return_separate_parts: bool = False) -> qutip.Qobj | tuple[qutip.Qobj, qutip.Qobj]:
    """
    Build the quantum Hamiltonian for EPR analysis.
    
    Takes linear mode frequencies and zero-point fluctuations to construct
    the full Hamiltonian matrix assuming cosine junction potential.
    """
    n_modes = len(frequencies_hz)
    n_junctions = len(inductances_h)

    zpfs = np.transpose(np.array(junction_flux_zpfs))  # Ensure J x N shape

    # creating lst of spaces and a composite space
    cspace = _create_composite_space(n_modes, fock_truncation)

    junction_energies_j = reduced_flux_quantum ** 2 / inductances_h
    junction_frequencies_hz = junction_energies_j / h

    _validate_hamiltonian_inputs(frequencies_hz, inductances_h, zpfs, n_modes, n_junctions)

    # Create mode operators
    mode_field_operators = _create_mode_field_operators(n_modes, fock_truncation)
    mode_number_operators = _create_mode_number_operators(n_modes, fock_truncation)

    # Build Hamiltonian parts
    linear_part = _create_linear_part(cspace, frequencies_hz)
    linear_part_old = dot_product(frequencies_hz, mode_number_operators)

    nonlinear_part_old = _build_nonlinear_hamiltonian_old(
        zpfs, mode_field_operators, junction_frequencies_hz, cosine_truncation
    )
    
    nonlinear_part = _build_nonlinear_hamiltonian(
        zpfs, cspace, junction_frequencies_hz, cosine_truncation
    )

    if return_separate_parts:
        return linear_part_old, nonlinear_part_old
    else:
        return linear_part_old + nonlinear_part_old


def _create_composite_space(n_modes: int, fock_truncation: int):
    # creating lst of spaces and a composite space
    spaces = [Space(size=fock_truncation, name=i) for i in range(n_modes)]
    return CompositeSpace(*spaces)


def _create_linear_part(cspace: CompositeSpace, frequencies_hz: NDArray):
    """
    creating number operator for each mode, expanding it (tensor with identity of the rest)
    and then multiplying with the frequency
    """
    ops = []
    for mode_number, frequency_hz in enumerate(frequencies_hz):
        space = cspace.spaces[mode_number]
        op = frequency_hz * cspace.expand_operator(mode_number, space.num_op())
        ops.append(op)

    return sum(ops)


def _build_nonlinear_hamiltonian(zpfs: NDArray,
                                 cspace: CompositeSpace,
                                 junction_frequencies_hz: NDArray,
                                 cosine_truncation: int) -> qutip.Qobj:
    """Build the nonlinear part of the Hamiltonian from cosine junction terms."""

    assert(len(zpfs) == len(junction_frequencies_hz))

    ops = []

    field_operators = [cspace.expand_operator(space.name, space.field_op())
                       for space in cspace.spaces_ordered]

    for zpf, junction_frequency_hz in zip(zpfs, junction_frequencies_hz):

        cosine_arg = np.dot(zpf, field_operators)
        cosine_op = cosine_taylor_series(cosine_arg, cosine_truncation)

        op = cosine_op * (-1) * junction_frequency_hz

        ops.append(op)

    return np.sum(ops)


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


def _build_nonlinear_hamiltonian_old(zpfs: np.ndarray, mode_field_operators: list[qutip.Qobj],
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
