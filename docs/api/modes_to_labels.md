# Modes to Labels

The `ModesToLabels` system assigns semantic labels to eigenmodes for quantum simulations. You can use either a simple dictionary or the full `ModesToLabels` class with inference strategies.

## Simple Dictionary Approach

For straightforward cases where you know the exact mode numbers:

```python
from quansys.simulation import QuantumEPR

# Simple mapping: mode number → label
epr = QuantumEPR(
    setup_name="eigenmode_setup",
    design_name="my_design", 
    modes_to_labels={1: "transmon", 2: "readout", 3: "bus"}
)
```

## ModesToLabels Class - Combined Strategy

For automatic mode labeling using multiple inference strategies:

```python
from quansys.simulation import QuantumEPR
from quansys.simulation.quantum_epr.modes_to_labels import (
    ModesToLabels, ManualInference, OrderInference
)

# Example eigenmode data
eigenmode_results = {
    1: {'frequency': 3.5, 'quality_factor': 100},
    2: {'frequency': 5.1, 'quality_factor': 120}, 
    3: {'frequency': 5.8, 'quality_factor': 90},
    4: {'frequency': 6.0, 'quality_factor': 150}
}

# Combined strategy: pin control manually + select lossy modes automatically
modes_to_labels = ModesToLabels(inferences=[
    ManualInference(mode_number=3, label="control"),           # Pin mode 3 as 'control'
    OrderInference(                                        # For remaining modes:
        num=2,                                             # Select 2 modes  
        min_or_max='min',                                  # With lowest Q (lossy)
        quantity='quality_factor',                         # Based on quality factor
        ordered_labels_by_frequency=['readout', 'purcell'] # Order by frequency
    )
])

result = modes_to_labels.parse(eigenmode_results)
print(result) # Output: {1: 'readout', 2: 'purcell', 3: 'control'}
# First execute all manual inferences, then order remaining modes by quality factor and frequency.
```

## Individual Inference Strategies

For detailed examples and usage patterns:

- **[ManualInference](manual_inference.md)**: Pin specific mode numbers to labels
- **[OrderInference](order_inference.md)**: Select modes by quality factor, order by frequency

## Execution Order

1. **ManualInference**: Applied first, assigns fixed mode numbers to specific labels
2. **OrderInference**: Applied to remaining modes, selects based on quality factor then orders by frequency

This ensures critical modes (like bus resonators) are always correctly labeled, while lossy modes are automatically identified and ordered.

::: quansys.simulation.quantum_epr.modes_to_labels.ModesToLabels