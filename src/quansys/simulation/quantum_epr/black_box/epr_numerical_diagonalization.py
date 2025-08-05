"""
Main entry point for EPR numerical diagonalization.
"""

from typing import Union, Optional
import numpy as np
import qutip

from .constants import reduced_flux_quantum
from .hamiltonian_builder import build_quantum_hamiltonian
from .dispersive_analysis import extract_dispersive_parameters


def calculate_quantum_parameters(mode_frequencies_ghz: np.ndarray, 
                               junction_inductances_h: np.ndarray,
                               reduced_flux_zpfs: np.ndarray, 
                               cosine_truncation: int = 8, 
                               fock_truncation: int = 9, 
                               return_hamiltonian: bool = False) -> Union[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray, qutip.Qobj]]:
    """
    Perform numerical diagonalization to extract quantum circuit parameters.
    
    This is the main function for EPR numerical analysis. It builds the quantum
    Hamiltonian and extracts dressed frequencies and dispersive shifts.
    
    Args:
        mode_frequencies_ghz: Linear mode frequencies in GHz, length M
        junction_inductances_h: Junction inductances in Henries, length J
        reduced_flux_zpfs: Reduced zero-point flux fluctuations (dimensionless), 
                          shape M x J
        cosine_truncation: Truncation order for cosine expansion (default=8)
        fock_truncation: Fock space truncation (default=9)  
        return_hamiltonian: If True, also return the Hamiltonian (default=False)
        
    Returns:
        tuple: (dressed_frequencies_ghz, chi_matrix_mhz) or 
               (dressed_frequencies_ghz, chi_matrix_mhz, hamiltonian) if return_hamiltonian=True
               
        - dressed_frequencies_ghz: Dressed mode frequencies in GHz
        - chi_matrix_mhz: Cross-Kerr matrix in MHz (sign flipped so down-shift is positive)
        - hamiltonian: Full quantum Hamiltonian (if requested)
    """
    frequencies = np.array(mode_frequencies_ghz)
    inductances = np.array(junction_inductances_h)
    zpfs = np.array(reduced_flux_zpfs)
    
    _validate_input_units(frequencies, inductances)
    
    # Convert to SI units for Hamiltonian construction
    frequencies_hz = frequencies * 1e9
    full_flux_zpfs = reduced_flux_quantum * zpfs  # Convert to full flux units
    
    # Build Hamiltonian
    hamiltonian = build_quantum_hamiltonian(
        frequencies_hz, 
        inductances.astype(float), 
        full_flux_zpfs,
        cosine_truncation=cosine_truncation,
        fock_truncation=fock_truncation
    )
    
    # Extract dispersive parameters
    dressed_freqs_hz, chi_hz, _, _ = extract_dispersive_parameters(
        hamiltonian, fock_truncation, zpfs, frequencies
    )
    
    # Convert to desired units
    dressed_freqs_ghz = dressed_freqs_hz * 1e-9  # Hz to GHz
    chi_mhz = -chi_hz * 1e-6  # Hz to MHz, flip sign so down-shift is positive
    
    if return_hamiltonian:
        return dressed_freqs_ghz, chi_mhz, hamiltonian
    else:
        return dressed_freqs_ghz, chi_mhz


def _validate_input_units(frequencies: np.ndarray, inductances: np.ndarray):
    """Validate that input units are correct."""
    if not (frequencies < 1e6).all():
        raise ValueError("Please provide frequencies in GHz (values should be < 1E6)")
    if not (inductances < 1e-3).all():
        raise ValueError("Please provide inductances in Henries (values should be < 1E-3)")


# Legacy alias for backward compatibility
epr_numerical_diagonalization = calculate_quantum_parameters