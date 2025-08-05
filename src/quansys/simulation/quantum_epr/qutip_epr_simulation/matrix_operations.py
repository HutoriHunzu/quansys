"""
Matrix operations for quantum Hamiltonian calculations.
"""

import qutip
from math import factorial


def cosine_matrix(operator):
    """
    Create exact cosine operator matrix using QutIP matrix exponentiation.
    
    Uses cos(x) = (e^(ix) + e^(-ix))/2 for exact calculation.
    """
    return 0.5 * ((1j * operator).expm() + (-1j * operator).expm())


def cosine_taylor_series(operator, max_order: int = 8):
    """
    Create Taylor series approximation of cosine.
    
    Uses cos(x) ≈ sum((-1)^n * x^(2n) / (2n)!) for n=0 to max_order.
    Note: Starts from n=2 to exclude constant and quadratic terms.
    """
    taylor_sum = qutip.qzero_like(operator)
    
    for n in range(2, max_order + 1):
        coefficient = (-1) ** n / factorial(2*n)
        taylor_sum += coefficient * (operator**(2*n))
    
    return taylor_sum