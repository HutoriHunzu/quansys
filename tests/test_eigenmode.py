import pytest
from quansys.simulation import EigenmodeAnalysis


NUM_OF_MODES_IN_SETUP = 5


def test_classical_result_mode_number(eigenmode_results):
    assert len(eigenmode_results.results) == NUM_OF_MODES_IN_SETUP

    prev_frequency = 0
    for mode_number, single_mode_result in eigenmode_results.results.items():
        assert mode_number == single_mode_result.mode_number
        assert prev_frequency <= single_mode_result.frequency.value
        assert (
            eigenmode_results.frequencies_unit.lower()
            == single_mode_result.frequency.unit.lower()
        )
        prev_frequency = single_mode_result.frequency.value


def test_classical_result_flat_types(eigenmode_results):
    flat_result = eigenmode_results.flatten()

    for k, v in flat_result.items():
        assert isinstance(k, str)
        assert isinstance(v, (str, bool, float))


def test_change_frequencies_unit(eigenmode_results):
    original_freq = eigenmode_results[1].frequency.value

    eigenmode_results.change_frequencies_unit("MHz")

    # Ensure unit is updated
    assert eigenmode_results.frequencies_unit.lower() == "mhz"
    assert eigenmode_results[1].frequency.unit.lower() == "mhz"
    assert eigenmode_results[1].frequency.value == pytest.approx(
        original_freq * 1000, rel=1e-3
    )


def test_generate_labeled_results(eigenmode_results):
    labeled = eigenmode_results.generate_a_labeled_version(
        {1: "Mode X", 2: "Mode Y", 3: "Mode Z", 4: "Mode A", 5: "Mode B"}
    )

    assert isinstance(labeled, type(eigenmode_results))
    assert labeled[0].label == "Mode X"
    assert labeled[4].label == "Mode B"
    assert labeled[0].mode_number == 0
    assert labeled[4].mode_number == 4


def test_generate_simple_form(eigenmode_results):
    simple_form = eigenmode_results.generate_simple_form()

    assert isinstance(simple_form, dict)
    assert list(simple_form.keys()) == list(eigenmode_results.results.keys())

    for k, v in simple_form.items():
        assert "frequency" in v
        assert "quality_factor" in v
        assert isinstance(v["frequency"], float)
        assert isinstance(v["quality_factor"], float)


def test_analyze_raises_on_invalid_hfss():
    sim = EigenmodeAnalysis(design_name="my_design", setup_name="Setup1")

    with pytest.raises(ValueError, match="hfss given must be a Hfss instance"):
        sim.analyze(hfss="not_a_valid_instance")


def test_frequencies_sorted(eigenmode_results):
    freqs = [mode.frequency.value for mode in eigenmode_results.results.values()]
    assert freqs == sorted(freqs), "Frequencies are not sorted ascending."
