# Manual Inference

ManualInference assigns a specific label to a specific mode number, regardless of its properties.

## Usage

To use an inference, call the `.infer()` method with eigenmode results:

```python
from quansys.simulation.quantum_epr.modes_to_labels import ManualInference

# Example eigenmode data  
eigenmode_results = {
    1: {'frequency': 3.5, 'quality_factor': 100},
    2: {'frequency': 5.1, 'quality_factor': 120}, 
}

# Create inference: always assign mode 2 as 'bus'
inference = ManualInference(mode_number=2, label="readout")

# Apply inference
result = inference.infer(eigenmode_results)
print(result)  # Output: {2: 'readout'}
```

!!! note "`.infer`"
    The method `.infer()` only validate the mode number exists in the eigenmode results.
    Any other properties of the mode (like frequency or quality factor) are ignored.


## Use Cases

- **Reference modes**: Fixed assignment for comparison across parameter sweeps
- **Can be chained**: can be combined with other inference strategies like `OrderInference` for more complex labeling scenarios

::: quansys.simulation.quantum_epr.modes_to_labels.ManualInference