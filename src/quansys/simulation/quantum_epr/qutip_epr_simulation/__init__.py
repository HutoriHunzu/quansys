"""
Quantum EPR black box calculations.

This module provides quantum parameter extraction through numerical diagonalization
of the full quantum Hamiltonian. The main entry point is calculate_quantum_parameters().
"""

from .epr_numerical_diagonalization import calculate_quantum_parameters

__all__ = [
    "calculate_quantum_parameters",
]
