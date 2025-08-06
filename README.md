# quansys

**Automated HFSS workflows for quantum circuit design and analysis**

[![Documentation](https://img.shields.io/badge/docs-github.io-blue)](https://hutorihunzu.github.io/quansys)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**quansys** is a Python package that automates HFSS electromagnetic simulations for quantum circuit analysis. It provides structured workflows for parameter sweeps, quantum parameter extraction via Energy Participation Ratio (EPR) analysis, and cluster-based execution.

## Features

- **Structured Workflows**: Automated prepare → build → simulate → aggregate pipeline
- **Parameter Sweeps**: Grid and custom parameter sweeps with caching and resumption
- **Quantum Analysis**: EPR-based quantum parameter extraction (χ matrix, dressed frequencies)
- **CLI Interface**: Command-line tools for simulation management and cluster execution
- **Result Processing**: Automatic JSON/CSV output generation for downstream analysis
- **Extensible**: Modular design supporting custom simulation types and builders

## Documentation

Complete documentation is available at: **[hutorihunzu.github.io/quansys](https://hutorihunzu.github.io/quansys)**

## Quick Start

### Installation

Install from PyPI:

```bash
pip install quansys
```

Or install from source:

```bash
git clone https://github.com/hutorihunzu/quansys.git
cd quansys
pip install -e .
```

### Basic Usage

1. **Create a simulation configuration** (`config.yaml`):

```yaml
pyaedt_file_parameters:
  file_path: "my_design.aedt"
  non_graphical: true

builder:
  type: 'design_variable_builder'
  design_name: "HfssDesign1"

builder_sweep:
  - type: 'DictSweep'
    parameters:
      resonator_length: ["10mm", "12mm", "14mm"]

simulations:
  eigenmode:
    type: 'eigenmode'
    design_name: "HfssDesign1"
    setup_name: "Setup1"
```

2. **Run the simulation**:

```bash
quansys run config.yaml
```

3. **Or use Python directly**:

```python
from quansys.workflow import WorkflowConfig, execute_workflow

config = WorkflowConfig.from_yaml("config.yaml")
execute_workflow(config)
```

## Simulation Types

### Eigenmode Analysis
Extract resonant frequencies and quality factors from electromagnetic eigenmodes:

```python
from quansys.simulation import EigenmodeAnalysis

simulation = EigenmodeAnalysis(
    design_name="HfssDesign1",
    setup_name="Setup1",
    cores=8
)
```

### Quantum EPR Analysis
Compute quantum circuit parameters using Energy Participation Ratio analysis:

```python
from quansys.simulation import QuantumEPR, ConfigJunction

simulation = QuantumEPR(
    design_name="HfssDesign1",
    setup_name="Setup1",
    modes_to_labels={0: "resonator", 1: "transmon"},
    junctions_infos=[ConfigJunction(line_name='my_jj_line', inductance_variable_name='lj')]
)
```

> **Note**: Quantum EPR analysis is based on the energy-participation-ratio method from: 
> ["Energy-participation quantization of Josephson circuits"](https://doi.org/10.1038/s41534-021-00461-8)

## Cluster Support

**quansys** is designed for high-performance computing environments and is currently optimized for **IBM LSF** cluster systems. The CLI provides tools for:

- Job preparation and submission
- Resource allocation management  
- Distributed execution across cluster nodes
- Result aggregation from multiple jobs

> **Cluster Requirement**: This package is specifically tailored for IBM LSF clusters. Support for other cluster systems (SLURM, PBS, etc.) may be added in future releases.

## Development

### Dependencies

- **HFSS/PyAEDT**: Electromagnetic simulation engine
- **QutIP**: Quantum parameter calculations
- **Typer**: CLI interface
- **Pydantic**: Configuration validation
- **Pandas/NumPy**: Data processing

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Quantum EPR Analysis**: Based on the energy-participation-ratio method developed in the pyEPR package. See: ["Energy-participation quantization of Josephson circuits"](https://doi.org/10.1038/s41534-021-00461-8)
- **HFSS Integration**: Built on top of [PyAEDT](https://github.com/ansys/pyaedt) for ANSYS Electronics Desktop automation