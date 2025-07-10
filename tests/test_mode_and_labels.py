import pytest
from pyhfss.simulation.quantum_epr import ManualInference, OrderInference, ModesAndLabels

@pytest.fixture
def mock_eigenmode_data():
    return {
        1: {'frequency': 3.5, 'quality_factor': 100},
        2: {'frequency': 5.1, 'quality_factor': 120},
        3: {'frequency': 5.8, 'quality_factor': 90},
        4: {'frequency': 6.0, 'quality_factor': 150}
    }


def test_manual_inference(mock_eigenmode_data):
    inference = ManualInference(mode_number=2, label='Readout')
    result = inference.infer(mock_eigenmode_data)

    assert result == {2: 'Readout'}


def test_manual_inference_invalid_mode(mock_eigenmode_data):
    inference = ManualInference(mode_number=99, label='Invalid')

    with pytest.raises(ValueError, match='mode not exists'):
        inference.infer(mock_eigenmode_data)


def test_order_inference_max_quality(mock_eigenmode_data):
    inference = OrderInference(
        num=2,
        min_or_max='max',
        ordered_labels_by_frequency=['A', 'B'],
        quantity='quality_factor'
    )

    result = inference.infer(mock_eigenmode_data)
    # top 2 quality: mode 4 (150), mode 2 (120) → assign A to 2 (sorted lower), B to 4
    assert result == {2: 'A', 4: 'B'}


def test_order_inference_min_quality(mock_eigenmode_data):
    inference = OrderInference(
        num=2,
        min_or_max='min',
        ordered_labels_by_frequency=['A', 'B'],
        quantity='quality_factor'
    )

    result = inference.infer(mock_eigenmode_data)
    # least 2 quality: mode 2 (90), mode 1 (100) → assign A to 1 (sorted lower), B to 3
    assert result == {1: 'A', 3: 'B'}


def test_order_inference_min_frequency(mock_eigenmode_data):
    inference = OrderInference(
        num=2,
        min_or_max='min',
        ordered_labels_by_frequency=['X', 'Y'],
        quantity='frequency'
    )

    result = inference.infer(mock_eigenmode_data)
    # lowest freqs: 3.5 (mode 1), 5.1 (mode 2)
    assert result == {1: 'X', 2: 'Y'}


def test_modes_and_labels_parse_combined(mock_eigenmode_data):
    modes_and_labels = ModesAndLabels(inferences=[
        ManualInference(mode_number=2, label='Bus'),
        OrderInference(
            num=2,
            min_or_max='max',
            ordered_labels_by_frequency=['Q1', 'Q2'],
            quantity='frequency'
        )
    ])

    parsed = modes_and_labels.parse(mock_eigenmode_data)

    # Manual takes 2 → Order selects top 2 freqs from remaining: mode 4 (6.0), 3 (5.8)
    assert parsed == {
        2: 'Bus',
        3: 'Q1',
        4: 'Q2'
    }
