from typing import Literal
from ansys.aedt.core.hfss import Hfss
from typing_extensions import Annotated
from pydantic import BeforeValidator, Field

from .distributed_analysis import DistributedAnalysis
from .epr_calculator import EprCalculator
from .modes_and_labels import ModesAndLabels
from pyhfss.simulation.base import (BaseAnalysis, SimulationTypesNames, validate_and_set_design)
from ..eigenmode.results import get_eigenmode_results

from .results import QuantumResults
from .structures import ConfigJunction, EprDiagResult, ParticipationDataset


def ensure_list(value):
    if not isinstance(value, list):
        return [value]
    return value


MODES_TO_LABELS_TYPE = ModesAndLabels | dict[int, str]
JUNCTION_INFO_TYPE = Annotated[list[ConfigJunction], BeforeValidator(ensure_list)]


class QuantumEpr(BaseAnalysis):
    """
    Runs an EPR-based quantum simulation using Eigenmode results and junction data.

    This analysis calculates energy participation ratios (EPR), anharmonicities,
    and the chi matrix for quantum circuit modes. It integrates multiple simulation
    stages into a high-level quantum post-processing workflow.

    Attributes:
        type: Simulation type identifier (always set to 'quantum_epr').
        design_name: Name of the HFSS design to use.
        setup_name: Name of the HFSS setup that has Eigenmode results.
        modes_to_labels: Either a parser or mapping from mode index to label.
        junctions_infos: Configuration objects describing the Josephson junctions.
    """

    type: Literal[SimulationTypesNames.QUANTUM_EPR] = SimulationTypesNames.QUANTUM_EPR
    design_name: str = Field(..., description="Design name in HFSS.")
    setup_name: str = Field(..., description="Setup name in HFSS.")
    modes_to_labels: MODES_TO_LABELS_TYPE = Field(..., description="Mode index-to-label mapping or parser.")
    junctions_infos: JUNCTION_INFO_TYPE = Field(..., description="List of junction configuration objects.")
    # type: Literal[SimulationTypesNames.QUANTUM_EPR] = SimulationTypesNames.QUANTUM_EPR
    # design_name: str
    # setup_name: str
    # modes_to_labels: MODES_TO_LABELS_TYPE
    # junctions_infos: JUNCTION_INFO_TYPE

    def analyze(self, hfss: Hfss) -> QuantumResults:
        """
        Run the full EPR simulation and return results.

        This includes distributed EM simulation, participation ratio extraction,
        and EPR matrix diagonalization.

        Args:
            hfss: An active HFSS project instance.

        Returns:
            QuantumResults: Final output containing EPR matrix, participation data, and labeled eigenmode results.

        Raises:
            ValueError: If `hfss` is not a valid Hfss instance.
        """

        if not isinstance(hfss, Hfss):
            raise ValueError('hfss given must be a Hfss instance')

        validate_and_set_design(hfss, self.design_name)

        # getting setup and getting
        setup = hfss.get_setup(self.setup_name)

        # getting eigenmode solution in simple form, meaning it is
        # of type dict[int, dict[str, float]
        # where the keys are the mode number and the values are frequency dict and quality factor dict
        eigenmode_result = get_eigenmode_results(setup)

        # convert modes to labels to dict of int to str
        # in case of ModesAndLabels object call for parse
        modes_to_labels = self.modes_to_labels

        if isinstance(modes_to_labels, ModesAndLabels):
            modes_to_labels = modes_to_labels.parse(eigenmode_result.generate_simple_form())

        epr, distributed = self._analyze(hfss, modes_to_labels)

        return QuantumResult(
            epr=epr,
            distributed=distributed,
            eigenmode_result=eigenmode_result.generate_a_labeled_version(modes_to_labels)
        )

    def _analyze(self, hfss: Hfss, modes_to_labels: dict[int, str]) -> tuple[EprDiagResult, ParticipationDataset]:
        dst = DistributedAnalysis(hfss,
                                  modes_to_labels=modes_to_labels,
                                  junctions_infos=self.junctions_infos)

        distributed_result = dst.main()

        calc = EprCalculator(participation_dataset=distributed_result)
        epr_result = calc.epr_numerical_diagonalizing()

        return epr_result, distributed_result


    def report(self):
        pass


