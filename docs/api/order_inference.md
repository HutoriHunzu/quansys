# Order Inference

OrderInference selects modes based on quality factor (or frequency), then assigns labels in frequency order.

## Usage

To use an inference, call the `.infer()` method with eigenmode results:

```python
from quansys.simulation.quantum_epr.modes_to_labels import OrderInference

# Example eigenmode data
eigenmode_results = {
    1: {'frequency': 3.5, 'quality_factor': 100},
    2: {'frequency': 5.1, 'quality_factor': 120}, 
    3: {'frequency': 5.8, 'quality_factor': 90},
    4: {'frequency': 6.0, 'quality_factor': 150}
}

# Select 2 lowest quality factor modes (readout/purcell)
inference = OrderInference(
    num=2,
    min_or_max='min',                          # Pick lowest Q modes
    quantity='quality_factor',
    ordered_labels_by_frequency=['readout', 'purcell']  # Lower freq → readout
)

result = inference.infer(eigenmode_results)
print(result)  # Output: {1: 'readout', 3: 'purcell'}
# Modes 3 and 1 have lowest Q (90, 100)  
# Assigning labels by frequency order:
# Mode 1 (freq 3.5) gets 'readout', Mode 3 (freq 5.8) gets 'purcell'
```

::: quansys.simulation.quantum_epr.modes_to_labels.OrderInference