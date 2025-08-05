"""
Physical constants for quantum EPR calculations.
"""

from scipy.constants import Planck, elementary_charge, pi

# Reduced Planck's constant
hbar = Planck / (2 * pi)

# Reduced flux quantum (phi_0/2pi in Webers)
reduced_flux_quantum = hbar / (2 * elementary_charge)