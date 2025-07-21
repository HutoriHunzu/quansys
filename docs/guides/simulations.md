# 🧪 Simulations Guide

This guide outlines the usage, design principles, and interfaces of the simulation classes provided in this package.

Currently supported simulation types:

- [EigenmodeAnalysis](../api/eigenmode_analysis.md)
- [QuantumEPR](../api/quantum_epr.md)

All simulation classes follow a consistent interface to ensure ease of use, automation, and result handling.

---

## Design Philosophy

!!! abstract "Unified Simulation Interface"
    All simulation classes conform to two core constraints:

    1. Implement an `.analyze(hfss)` method that runs the simulation.
    2. Return a **JSON-serializable** object that supports **flattening** for aggregation.

This approach enables uniform integration into pipelines, simplifies logging, and supports downstream analysis (e.g., storing results in databases or converting to tables using Pandas).

---

!!! note "About Flattening"
    The `.flatten()` method converts the result into a flat dictionary with simple key-value pairs.  
    This is useful for aggregation or tabular data storage but may omit nested information.

    For full data preservation, use:

    ```python
    result.model_dump()        # Full result as a nested dict
    result.model_dump_json()   # JSON-formatted string
    ```

    Use `.flatten()` primarily for aggregation, and `.model_dump()` or `.model_dump_json()` for saving or inspection.

---

??? note "CPU Configuration"
    The [Eigenmode Analysis](../api/eigenmode_analysis.md) class includes a `cores` attribute. 
    This can be used to control how many CPU cores are requested or used, particularly useful when submitting jobs to a computing cluster.

---

## Using Simulation Classes

!!! example "Importing and Executing a Simulation"
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
