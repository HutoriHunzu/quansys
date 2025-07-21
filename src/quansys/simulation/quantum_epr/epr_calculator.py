import numpy as np
from scipy.constants import Planck, elementary_charge, pi  # pylint: disable=unused-import

import warnings
from .structures import ParticipationDataset, EprDiagResult
from .black_box import black_box_numeric as black_box

# Reduced Planks constant
hbar = Planck / (2 * pi)

# Reduced Flux Quantum  (3.29105976 × 10-16 Webers)
reduced_flux_quantum = hbar / (2 * elementary_charge)


class EprCalculator:

    def __init__(self, participation_dataset: ParticipationDataset):
        self.participation_dataset = participation_dataset

    def get_epr_base_matrices(self):
        res = self._normalize_participation()
        PJ = np.array(res['PJ'])
        PJ_cap = np.array(res['PJ_cap'])

        # Sign bits
        sign = self.participation_dataset.sign.copy()  # DataFrame
        #  Frequencies of HFSS linear modes.
        #  Input in dataframe but of one line. Output nd array
        frequencies = np.diagflat(self.participation_dataset.frequencies) / 1e9  # GHz
        # Junction energies
        inductances = self.participation_dataset.inductances
        capacitances = self.participation_dataset.capacitances

        junction_inductance_energy_ghz = 10 ** -9 * (reduced_flux_quantum ** 2) / (inductances * Planck)
        junction_inductance_energy_ghz = np.diagflat(junction_inductance_energy_ghz)  # GHz

        junction_capacitance_energy_ghz = elementary_charge ** 2 / (capacitances * Planck)
        junction_capacitance_energy_ghz = np.diagflat(junction_capacitance_energy_ghz)

        phi_zpf = sign * np.sqrt(0.5 * frequencies @ PJ @ np.linalg.inv(junction_inductance_energy_ghz))
        n_zpf = sign * np.sqrt(frequencies @ PJ @ np.linalg.inv(junction_capacitance_energy_ghz) / (4 * 4))

        return PJ, sign, frequencies, junction_inductance_energy_ghz, phi_zpf, PJ_cap, n_zpf

    def _normalize_participation(self):

        participation_ratio_induction = self.participation_dataset.participation_ratio_induction.copy()
        participation_ratio_capacitance = self.participation_dataset.participation_ratio_capacitance.copy()
        total_inductance_energy = self.participation_dataset.total_inductance_energy.copy()
        total_capacitance_energy = self.participation_dataset.total_capacitance_energy.copy()
        peak_total_magnetic_energy = self.participation_dataset.peak_total_magnetic_energy.copy()
        peak_total_electric_energy = self.participation_dataset.peak_total_electric_energy.copy()

        # Renormalize
        # Should we still do this when Pm_glb_sum is very small
        # s = self.sols[variation]
        # sum of participation energies as calculated by global UH and UE
        # U_mode = s['U_E'] # peak mode energy; or U bar as i denote it sometimes
        # We need to add the capacitor here, and maybe take the mean of that

        u_mode = (total_inductance_energy + total_capacitance_energy) / 2.
        u_diff = abs(total_capacitance_energy - total_inductance_energy) / u_mode
        if np.any(u_diff > 0.15):
            warnings.warn(f"WARNING: U_tot_cap-U_tot_ind / mean = {np.max(np.abs(u_diff)) * 100:.1f}% is > 15%. \
                \nIs the simulation converged? Proceed with caution")

        # global sums of participations
        Pm_glb_sum = abs((u_mode - peak_total_magnetic_energy) / u_mode)
        Pm_cap_glb_sum = abs((u_mode - peak_total_electric_energy) / u_mode)

        # norms
        Pm_norm = Pm_glb_sum / participation_ratio_induction.sum(axis=1)
        Pm_cap_norm = Pm_cap_glb_sum / participation_ratio_capacitance.sum(axis=1)
        # this is not the correct scaling yet! WARNING. Factors of 2 laying around too
        # these numbers are a bit all over the place for now. very small

        idx = participation_ratio_induction > 0.15  # Mask for where to scale
        idx_cap = participation_ratio_capacitance > 0.15

        pm_norm_expanded = np.tile(Pm_norm[:, None], participation_ratio_induction.shape[1])
        pm_cap_norm_expanded = np.tile(Pm_cap_norm[:, None], participation_ratio_capacitance.shape[1])

        participation_ratio_induction[idx] *= pm_norm_expanded[idx]
        participation_ratio_capacitance[idx_cap] *= pm_cap_norm_expanded[idx_cap]
        # Pm = Pm.mul(Pm_norm, axis=0)
        # Pm_cap = Pm_cap.mul(Pm_cap_norm, axis=0)

        if np.any(participation_ratio_induction < 0.0):
            warnings.warn("  ! Warning:  Some p_mj was found <= 0. This is probably a numerical error,'\
                'or a super low-Q mode.  We will take the abs value.  Otherwise, rerun with more precision,'\
                'inspect, and do due diligence.)")
            # print(Pm, '\n')
            # Pm = np.abs(Pm)

        return {'PJ': participation_ratio_induction,
                'Pm_norm': Pm_norm,
                'PJ_cap': participation_ratio_capacitance,
                'Pm_cap_norm': Pm_cap_norm,
                'idx': idx,
                'idx_cap': idx_cap}

    def epr_numerical_diagonalizing(self):

        PJ, sign, frequencies_mat, junction_inductance_energy_ghz, phi_zpf, PJ_cap, n_zpf = self.get_epr_base_matrices()
        frequencies_ghz = self.participation_dataset.frequencies / 1e9

        f1_nd, chi_nd = black_box.epr_numerical_diagonalization(frequencies_ghz,
                                                                self.participation_dataset.inductances,
                                                                phi_zpf, cos_trunc=8, fock_trunc=15)

        return EprDiagResult(chi=chi_nd, frequencies=f1_nd * 1e-9)
