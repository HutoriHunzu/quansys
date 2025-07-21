# 🧪 Simulations Guide

This guide explains how to use the simulation classes provided in this package. It includes a quickstart example, how to handle results, and design principles.

---

## ✅ Supported Simulation Types

The package currently supports the following simulations:

- [`EigenmodeAnalysis`](../api/eigenmode_analysis.md)  
- [`QuantumEPR`](../api/quantum_epr.md)

All simulation classes follow a consistent interface to make automation, result handling, and integration simple and predictable.

---

## 🚀 Quickstart Example

Let’s walk through how to run a basic simulation using the `EigenmodeAnalysis` class.

1. Make sure the `quansys` package is installed and your virtual environment is activated.
 
2. Create a simple AEDT design for the simulation. From your terminal:

    ```bash
    quansys example
    ```
    This command generates:

    - `simple_design.aedt`: a basic HFSS design with a single resonator.
   
    - `config.yml`: an automation config (see the [automation guide](automation.md)).

3. Create a Python script with the following content:

!!! example "Running a Simulation"
    ```python
    from quansys.simulation import EigenmodeAnalysis

    analysis = EigenmodeAnalysis(
        design_name="MyDesign",
        setup_name="Setup1"
    )

    result = analysis.analyze(hfss)

    # Access specific results
    result.results[1].quality_factor    # Quality factor for mode 1
    result.results[1].frequency         # Frequency for mode 1

    # For saving or aggregation, see .model_dump(), .flatten(), etc.
    ```

---

## 📤 Accessing & Saving Results

Simulation results are returned as structured objects, with methods for exporting and inspection:

- `result.model_dump()` → Full result as a nested Python dictionary.
- `result.model_dump_json()` → Same, but in JSON string format.
- `result.flatten()` → A flat dictionary (key-value pairs) for easy storage or tabular conversion.

Use `.flatten()` for quick aggregation (e.g., pandas DataFrame), and `.model_dump()` for full detail or archival.

---

## 🔄 Serialization & Flattening

!!! note "About Flattening"
    The `.flatten()` method simplifies a result into a flat dictionary.  
    This is ideal for storing in databases or converting to tables — but it may drop nested structure.

    For complete data retention:
    ```python
    result.model_dump()        # Full nested dictionary
    result.model_dump_json()   # JSON-formatted string
    ```

---

## 🧠 Design Philosophy

!!! abstract "Unified Simulation Interface"
    All simulation classes follow these two core rules:

    1. They implement an `.analyze(hfss)` method to run the simulation.
    2. They return a **JSON-serializable** result that supports `.flatten()` for aggregation.

This design allows easy integration into automation pipelines and downstream processing (e.g., logging, analysis, and visualization).

---

## ⚙️ Advanced Notes

??? note "CPU Configuration"
    The [`EigenmodeAnalysis`](../api/eigenmode_analysis.md) class includes a `cores` attribute.  
    This can be used to control how many CPU cores are requested — especially useful in cluster environments.

---

