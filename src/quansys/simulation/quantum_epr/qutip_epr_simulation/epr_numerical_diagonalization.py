"""
Main entry point for EPR numerical diagonalization.
"""

import numpy as np

from .constants import reduced_flux_quantum
from .hamiltonian_builder import build_quantum_hamiltonian
from .dispersive_analysis import extract_dispersive_parameters
from .space import Space
from .composite_space import CompositeSpace


def calculate_quantum_parameters(
    mode_frequencies_ghz: np.ndarray,
    junction_inductances_h: np.ndarray,
    reduced_flux_zpfs: np.ndarray,
    cosine_truncation: int = 8,
    fock_truncation: int = 9,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Perform numerical diagonalization to extract quantum circuit parameters.

    Based on the energy-participation-ratio (EPR) method from:
    "Energy-participation quantization of Josephson circuits"
    DOI: https://doi.org/10.1038/s41534-021-00461-8


    Builds the full quantum Hamiltonian H = H_linear + H_junction where:
    - H_linear = sum(omega_i * n_i) for harmonic oscillator terms
    - H_junction = -sum(E_J * cos(phi_zpf_i * (a_i + a_i_dag) / phi_0)) for Josephson interactions

    The method numerically diagonalizes the Hamiltonian to extract dressed mode
    frequencies and cross-Kerr interaction strengths (chi matrix).

    Args:
        mode_frequencies_ghz: Linear mode frequencies in GHz, length M
        junction_inductances_h: Junction inductances in Henries, length J
        reduced_flux_zpfs: Reduced zero-point flux fluctuations (dimensionless),
                          shape M x J
        cosine_truncation: Truncation order for cosine expansion (default=8)
        fock_truncation: Fock space truncation (default=9)

    Returns:
        tuple: (dressed_frequencies_ghz, chi_matrix_mhz)

        - dressed_frequencies_ghz: Dressed mode frequencies in GHz
        - chi_matrix_mhz: Cross-Kerr matrix in MHz (sign flipped so down-shift is positive)
    """
    frequencies = np.array(mode_frequencies_ghz)
    inductances = np.array(junction_inductances_h)
    zpfs = np.array(reduced_flux_zpfs)

    _validate_input_units(frequencies, inductances)

    # Convert to SI units for Hamiltonian construction
    frequencies_hz = frequencies * 1e9
    full_flux_zpfs = reduced_flux_quantum * zpfs  # Convert to full flux units

    # creating spaces
    n_modes = len(frequencies)
    cspace = _create_composite_space(n_modes=n_modes, fock_truncation=fock_truncation)

    # Build Hamiltonian
    hamiltonian = build_quantum_hamiltonian(
        cspace,
        frequencies_hz,
        inductances.astype(float),
        full_flux_zpfs,
        cosine_truncation=cosine_truncation,
    )

    # Extract dispersive parameters
    dressed_freqs_hz, chi_hz, _, _ = extract_dispersive_parameters(
        cspace, hamiltonian, fock_truncation, zpfs, frequencies
    )

    # Convert to desired units
    dressed_freqs_ghz = dressed_freqs_hz * 1e-9  # Hz to GHz
    chi_mhz = -chi_hz * 1e-6  # Hz to MHz, flip sign so down-shift is positive

    return dressed_freqs_ghz, chi_mhz


def _validate_input_units(frequencies: np.ndarray, inductances: np.ndarray):
    """Validate that input units are correct."""
    if not (frequencies < 1e6).all():
        raise ValueError("Please provide frequencies in GHz (values should be < 1E6)")
    if not (inductances < 1e-3).all():
        raise ValueError(
            "Please provide inductances in Henries (values should be < 1E-3)"
        )


def _create_composite_space(n_modes: int, fock_truncation: int) -> CompositeSpace:
    """Create composite space for the quantum system."""
    spaces = [Space(size=fock_truncation, name=i) for i in range(n_modes)]
    return CompositeSpace(*spaces)
