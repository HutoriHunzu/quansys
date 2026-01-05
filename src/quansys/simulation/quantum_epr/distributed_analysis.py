from pathlib import Path
from typing import List, Tuple

import numpy as np
from ansys.aedt.core.hfss import Hfss
from ansys.aedt.core.visualization.post.post_common_3d import PostProcessor3D
from numpy.typing import NDArray

from quansys.simulation.eigenmode.results import EigenmodeResults

from .structures import (
    ConfigJunction,
    ParsedJunctionValues,
    ParticipationDataset,
    ParticipationJunctionDataset,
    variables_types,
)


def inverse_dict(d: dict):
    # check all values are unique and are immutable
    values = list(d.values())
    assert len(values) == len(set(values))
    try:
        list(map(lambda x: hash(x), values))
    except TypeError:
        raise TypeError(f"Cannot inverse dict as values are not immutables: {d}")

    return {v: k for k, v in d.items()}

    pass


def read_and_delete(filepath):
    f = Path(filepath)
    txt = f.read_text()
    f.unlink()
    return txt


def parse_expression_filetxt(txt):
    return float(txt.split()[-1])


def calculator_read(calculator, expression_name):
    return float(calculator.evaluate(expression_name))


class DistributedAnalysis:
    def __init__(
        self, hfss: Hfss, modes_to_labels: dict, junctions_infos: List[ConfigJunction]
    ):
        self.hfss = hfss
        self.post_api: PostProcessor3D = hfss.post
        self.field_calculator = self.post_api.fields_calculator
        self.modes_to_labels = modes_to_labels
        self.labels_to_modes = inverse_dict(modes_to_labels)
        self.junctions_infos = tuple(junctions_infos)
        self.number_of_modes = None

    def add_expression(self, expr, assignment=""):
        if not self.field_calculator.is_expression_defined(expr["name"]):
            v = self.field_calculator.add_expression(expr, assignment)
            if not v:
                raise ValueError(
                    f"Couldn't add expression {expr}, "
                    f"check if assignment = {assignment} appears in the design"
                )

    def calc_total_electric_energy(self, use_smooth=False):
        add_electric_field = ["Fundamental_Quantity('E')"]
        if use_smooth:
            add_electric_field += ["Operation('Smooth')"]

        expression_name = "total_electric_energy"

        expression = {
            "name": expression_name,
            "description": "Voltage drop along a line",
            "design_type": ["HFSS"],
            "fields_type": ["Fields"],
            "solution_type": "",
            "primary_sweep": "Freq",
            "assignment": "",
            "assignment_type": ["Solid"],
            "operations": [
                "Fundamental_Quantity('E')",
                "MaterialOp('Permittivity (epsi)', 1)",
                "Fundamental_Quantity('E')",
                "Operation('Conj')",
                "Operation('Dot')",
                "Operation('Real')",
                "EnterVolume('AllObjects')",
                "Operation('VolumeValue')",
                "Operation('Integrate')",
            ],
            "report": ["Data Table", "Rectangular Plot"],
        }

        self.add_expression(expression)

        return calculator_read(self.field_calculator, expression_name)

    def calc_total_magnetic_energy(self, use_smooth=False):
        add_magnetic_field = ["NameOfExpression('<Hx,Hy,Hz>')"]
        if use_smooth:
            add_magnetic_field += ["Operation('Smooth')"]

        expression_name = "total_magnetic_energy"
        expression = {
            "name": expression_name,
            "description": "Voltage drop along a line",
            "design_type": ["HFSS"],
            "fields_type": ["Fields"],
            "solution_type": "",
            "primary_sweep": "Freq",
            "assignment": "",
            "assignment_type": ["Solid"],
            "operations": add_magnetic_field
            + ["MaterialOp('Permeability (mu)', 1)"]
            + add_magnetic_field
            + [
                "Operation('Conj')",
                "Operation('Dot')",
                "Operation('Real')",
                "EnterVolume('AllObjects')",
                "Operation('VolumeValue')",
                "Operation('Integrate')",
            ],
            "report": ["Data Table", "Rectangular Plot"],
        }

        self.add_expression(expression)
        return calculator_read(self.field_calculator, expression_name)

    def set_mode(self, mode):
        mode = str(mode)
        one_hot_mode_dict = {
            f"{i}": ("0", "0deg") for i in range(1, self.number_of_modes + 1)
        }
        one_hot_mode_dict[mode] = ("1", "0deg")

        # edit sources such that it is only one active
        self.hfss.edit_sources(
            assignment=one_hot_mode_dict, eigenmode_stored_energy=False
        )

    def _calculate_line_voltage(
        self, freq, line_object_name, line_inductance, use_smooth=False
    ):
        add_electric_field = ["Fundamental_Quantity('E')"]
        if use_smooth:
            add_electric_field += ["Operation('Smooth')"]

        expression_name_real = f"current_line_e_real_{line_object_name}"
        expression_name_imag = f"current_line_e_imag_{line_object_name}"

        expression_real = {
            "name": expression_name_real,
            "description": "Current along a line",
            "design_type": ["HFSS", "Q3D Extractor"],
            "fields_type": ["Fields", "CG Fields"],
            "solution_type": "",
            "primary_sweep": "Freq",
            "assignment": "",
            "assignment_type": ["Line"],
            "operations": add_electric_field
            + [
                "Operation('Real')",
                "Operation('Tangent')",
                "Operation('Dot')",
                "EnterLine('assignment')",
                "Operation('LineValue')",
                "Operation('Integrate')",
            ],
            "dependent_expressions": [],
            "report": ["Data Table", "Rectangular Plot"],
        }

        expression_imag = {
            "name": expression_name_imag,
            "description": "Current along a line",
            "design_type": ["HFSS", "Q3D Extractor"],
            "fields_type": ["Fields", "CG Fields"],
            "solution_type": "",
            "primary_sweep": "Freq",
            "assignment": "",
            "assignment_type": ["Line"],
            "operations": add_electric_field
            + [
                "Operation('Imag')",
                "Operation('Tangent')",
                "Operation('Dot')",
                "EnterLine('assignment')",
                "Operation('LineValue')",
                "Operation('Integrate')",
            ],
            "dependent_expressions": [],
            "report": ["Data Table", "Rectangular Plot"],
        }

        self.add_expression(expression_real, assignment=line_object_name)
        self.add_expression(expression_imag, assignment=line_object_name)
        v_real = calculator_read(self.field_calculator, expression_name_real)
        v_imag = calculator_read(self.field_calculator, expression_name_imag)

        peak_voltage = np.sign(v_real) * np.sqrt(v_real**2 + v_imag**2)
        omega = 2 * np.pi * freq
        impedance = omega * line_inductance
        return peak_voltage / impedance, peak_voltage

    def parse_modes_and_set_number_of_modes(self, eigenmode_result):
        modes = set(eigenmode_result.keys())

        self.number_of_modes = len(modes)

        # checking that the required modes appear in the supported list
        modes_from_labels = set(self.modes_to_labels.keys())
        if not modes_from_labels <= modes:
            raise ValueError(
                f"Selected modes {modes_from_labels} is not subset of available modes {modes}"
            )

    # def get_mode_frequency_and_q_factor(self, mode_number):
    #     freq_sol = self.post_api.get_solution_data(expressions=f"Mode({mode_number})")
    #     q_sol = self.post_api.get_solution_data(expressions=f"Q({mode_number})")
    #     return freq_sol.data_real()[0], q_sol.data_real()[0]

    def calculate_peak_current_and_voltage(
        self, mode_frequency, junction_infos: Tuple[ParsedJunctionValues, ...]
    ):
        def helper():
            for info in junction_infos:
                yield self._calculate_line_voltage(
                    mode_frequency, info.info.line_name, info.inductance.value
                )

        peak_currents, peak_voltages = list(zip(*helper()))

        return np.array(peak_currents), np.array(peak_voltages)

    def calculate_inductance_and_capacitance_energies(
        self,
        peak_currents: NDArray,
        peak_voltages: NDArray,
        infos: Tuple[ParsedJunctionValues, ...],
    ):
        inductances = np.array(list(map(lambda x: x.inductance.value, infos)))
        capacitances = np.array(list(map(lambda x: x.capacitance.value, infos)))

        inductance_energy = 0.5 * inductances * peak_currents**2
        capacitance_energy = 0.5 * capacitances * peak_voltages**2

        return inductance_energy, capacitance_energy

    def calculate_p_junction(
        self,
        mode_frequency,
        two_times_total_peak_magnetic_energy,
        two_times_total_peak_electric_energy,
        junctions_infos: Tuple[ParsedJunctionValues, ...],
    ):
        junctions_infos = tuple(junctions_infos)

        peak_total_magnetic_energy = two_times_total_peak_magnetic_energy / 2
        peak_total_electric_energy = two_times_total_peak_electric_energy / 2

        # calculate peak current for every junction info
        peak_currents, peak_voltages = self.calculate_peak_current_and_voltage(
            mode_frequency, junctions_infos
        )

        # calculate inductance and capacitance energies
        inductance_energy, capacitance_energy = (
            self.calculate_inductance_and_capacitance_energies(
                peak_currents, peak_voltages, junctions_infos
            )
        )

        total_inductance_energy = peak_total_magnetic_energy + inductance_energy.sum()
        total_capacitance_energy = peak_total_electric_energy + capacitance_energy.sum()

        norm = total_capacitance_energy
        diff = (total_capacitance_energy - total_inductance_energy) / (
            total_capacitance_energy + total_inductance_energy
        )

        participation_ratio_induction = inductance_energy / norm

        participation_ratio_capacitance = capacitance_energy / norm

        sign = np.sign(peak_voltages)

        return ParticipationJunctionDataset(
            junctions_infos=junctions_infos,
            participation_ratio_capacitance=participation_ratio_capacitance,
            participation_ratio_induction=participation_ratio_induction,
            sign=sign,
            peak_currents=peak_currents,
            peak_voltages=peak_voltages,
            inductance_energy=inductance_energy,
            capacitance_energy=capacitance_energy,
            total_inductance_energy=total_inductance_energy,
            total_capacitance_energy=total_capacitance_energy,
            peak_total_magnetic_energy=peak_total_magnetic_energy,
            peak_total_electric_energy=peak_total_electric_energy,
            norm=norm,
            diff=diff,
        )

    def get_all_frequencies_and_q_factors_with_labels(
        self, eigenmode_result: dict[int, dict[str, float]]
    ):
        return {
            label: {
                "freq": eigenmode_result[mode_number]["frequency"],
                "q_factor": eigenmode_result[mode_number]["quality_factor"],
            }
            for mode_number, label in self.modes_to_labels.items()
        }

    def get_inductance_and_capacitance(self, inductance_variable_name):
        inductance = self.hfss.get_evaluated_value(inductance_variable_name)
        capacitance = 2e-15
        return inductance, capacitance

    def _parse_junctions_infos_to_values(
        self, label_to_freq_and_qfactor
    ) -> Tuple[ParsedJunctionValues, ...]:
        def helper():
            for info in self.junctions_infos:
                inductance, capacitance = self.get_inductance_and_capacitance(
                    info.inductance_variable_name
                )

                yield ParsedJunctionValues(
                    info=info,
                    inductance=variables_types.Value(value=inductance, unit="H"),
                    capacitance=variables_types.Value(value=capacitance, unit=""),
                )

        return tuple(helper())

    def main(
        self, eigenmode_result: dict[int, dict[str, float]]
    ) -> ParticipationDataset:
        # parsing to make sure the total number of modes is correct
        self.parse_modes_and_set_number_of_modes(eigenmode_result)

        # getting frequencies and q factors for all modes
        label_to_frequency_and_q_factor = (
            self.get_all_frequencies_and_q_factors_with_labels(eigenmode_result)
        )

        # parsing junctions infos into parsed junction values
        parsed_junction_infos = self._parse_junctions_infos_to_values(
            label_to_frequency_and_q_factor
        )

        result = {}

        # for each mode
        for mode_number, label in self.modes_to_labels.items():
            # set mode
            self.set_mode(mode_number)

            # freq and q factor
            two_times_total_peak_magnetic_energy = self.calc_total_magnetic_energy()
            two_times_peak_total_electric_energy = self.calc_total_electric_energy()

            # get current mode frequency
            frequency = label_to_frequency_and_q_factor[label]["freq"]  # SI

            # calculate p junction
            result[label] = self.calculate_p_junction(
                frequency,
                two_times_total_peak_magnetic_energy,
                two_times_peak_total_electric_energy,
                parsed_junction_infos,
            )

        participation_dataset = ParticipationDataset.from_participation_junctions(
            result, self.labels_to_modes, label_to_frequency_and_q_factor
        )

        return participation_dataset
