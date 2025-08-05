"""
Quantum EPR black box calculations.

This module provides quantum parameter extraction through numerical diagonalization
of the full quantum Hamiltonian. The main entry point is calculate_quantum_parameters().
"""

from .black_box_numeric import (
    epr_numerical_diagonalization
)

__all__ = [
    'epr_numerical_diagonalization',
]