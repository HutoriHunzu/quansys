from typing import Dict, Tuple, Any, List
from numpy.typing import NDArray
from dataclasses import dataclass, field
from ..config_handler.junction_scheme import ConfigJunction
from ..config_handler.variable_scheme import ValuedVariable
import numpy as np


@dataclass
class EprDiagResult:
    chi: NDArray
    frequencies: NDArray


@dataclass
class ParsedJunctionValues:
    info: ConfigJunction
    inductance: ValuedVariable
    capacitance: ValuedVariable = field(default_factory=lambda: ValuedVariable(2e-15))


# T = TypeVar('T', bound='ParticipationDataset')


@dataclass
class ParticipationJunctionDataset:
    junctions_infos: Tuple[ParsedJunctionValues, ...]

    participation_ratio_induction: NDArray
    participation_ratio_capacitance: NDArray
    sign: NDArray
    peak_currents: NDArray
    peak_voltages: NDArray
    inductance_energy: NDArray
    capacitance_energy: NDArray
    total_inductance_energy: float
    total_capacitance_energy: float
    peak_total_magnetic_energy: float
    peak_total_electric_energy: float
    norm: float
    diff: float


@dataclass
class ParticipationDataset:
    junctions_infos: Tuple[ParsedJunctionValues, ...]
    labels_to_modes: Dict[str, int]
    labels_order: Tuple[str, ...]
    frequencies: NDArray
    quality_factors: NDArray
    inductances: NDArray
    capacitances: NDArray

    participation_ratio_induction: NDArray
    participation_ratio_capacitance: NDArray
    sign: NDArray
    peak_currents: NDArray
    peak_voltages: NDArray
    inductance_energy: NDArray
    capacitance_energy: NDArray
    total_inductance_energy: NDArray
    total_capacitance_energy: NDArray
    peak_total_magnetic_energy: NDArray
    peak_total_electric_energy: NDArray
    norm: NDArray
    diff: NDArray

    @classmethod
    def from_participation_junctions(
            cls, label_to_junction_dataset_dict: Dict[str, ParticipationJunctionDataset],
            labels_to_modes: Dict[str, int],
            labels_to_freq_and_quality_factors: Dict[str, Dict[str, float | int]]) -> 'ParticipationDataset':

        if not label_to_junction_dataset_dict:
            raise ValueError("No instances provided for merging.")

        junctions_infos = list(label_to_junction_dataset_dict.values())[
            0].junctions_infos  # Assuming all have the same junctions_infos

        # Initialize lists to collect each attribute
        participation_ratio_induction = []
        participation_ratio_capacitance = []
        sign = []
        peak_currents = []
        peak_voltages = []
        inductance_energy = []
        capacitance_energy = []
        total_inductance_energy = []
        total_capacitance_energy = []
        peak_total_magnetic_energy = []
        peak_total_electric_energy = []
        norm = []
        diff = []
        labels_order = []
        frequencies = []
        quality_factors = []
        inductances = []
        capacitances = []

        # junctions_dict = dict(list(map(lambda x: (x.info.name, x), junctions_infos)))

        for label, instance in label_to_junction_dataset_dict.items():
            labels_order.append(label)
            participation_ratio_induction.append(instance.participation_ratio_induction)
            participation_ratio_capacitance.append(instance.participation_ratio_capacitance)
            sign.append(instance.sign)
            peak_currents.append(instance.peak_currents)
            peak_voltages.append(instance.peak_voltages)
            inductance_energy.append(instance.inductance_energy)
            capacitance_energy.append(instance.capacitance_energy)
            total_inductance_energy.append(instance.total_inductance_energy)
            total_capacitance_energy.append(instance.total_capacitance_energy)
            peak_total_magnetic_energy.append(instance.peak_total_magnetic_energy)
            peak_total_electric_energy.append(instance.peak_total_electric_energy)
            norm.append(instance.norm)
            diff.append(instance.diff)
            frequencies.append(labels_to_freq_and_quality_factors[label]['freq'])
            quality_factors.append(labels_to_freq_and_quality_factors[label]['q_factor'])

        for junction in junctions_infos:
            capacitances.append(junction.capacitance.value)
            inductances.append(junction.inductance.value)

        return cls(
            junctions_infos=junctions_infos,
            labels_to_modes=labels_to_modes,
            labels_order=tuple(labels_order),
            participation_ratio_induction=np.vstack(participation_ratio_induction),
            participation_ratio_capacitance=np.vstack(participation_ratio_capacitance),
            sign=np.vstack(sign),
            peak_currents=np.vstack(peak_currents),
            peak_voltages=np.vstack(peak_voltages),
            inductance_energy=np.vstack(inductance_energy),
            capacitance_energy=np.vstack(capacitance_energy),
            total_inductance_energy=np.array(total_inductance_energy),
            total_capacitance_energy=np.array(total_capacitance_energy),
            peak_total_magnetic_energy=np.array(peak_total_magnetic_energy),
            peak_total_electric_energy=np.array(peak_total_electric_energy),
            norm=np.array(norm),
            diff=np.array(diff),
            quality_factors=np.array(quality_factors),
            frequencies=np.array(frequencies),
            capacitances=np.array(capacitances),
            inductances=np.array(inductances)
        )


@dataclass
class QuantumResult:
    epr: EprDiagResult
    distributed: ParticipationDataset
