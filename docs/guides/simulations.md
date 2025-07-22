# 🧪 Simulation Guide

This page shows how to run the two built‑in simulation classes, inspect their results, and understand the design rules behind them.

!!! info "Prerequisite"
    You need an **HFSS project** (`.aedt`) in your working directory and you must know its **design name** and **setup name**.  
    The [Quick‑Start guide](../getting_started.md) can copy two ready‑made projects:

    - **simple_design.aedt** — `my_design` / `Setup1` (used in Example 1)  
    - **complex_design.aedt** — `my_design` / `Setup1` (used in Example 2)

---

## Supported classes

- [`EigenmodeAnalysis`](../api/eigenmode_analysis.md)  
- [`QuantumEPR`](../api/quantum_epr.md)

Both share the same interface, so you can swap them with minimal code edits.

---

## Example 1: Eigenmode analysis (simple design)

Save the snippet below to `run_eigen.py` and execute it.  
It opens **`simple_design.aedt`**, runs **`Setup1`**, then prints the Q‑factor and frequency of mode 1.

!!! example "run_eigen.py"
    ```python
    from quansys.simulation import EigenmodeAnalysis
    from quansys.workflow import PyaedtFileParameters

    params = PyaedtFileParameters(
        "simple_design.aedt",
        design_name="my_design",
        non_graphical=True   # headless HFSS
    )

    eigen = EigenmodeAnalysis("my_design", "Setup1")

    with params.open_pyaedt_file() as hfss:
        result = eigen.analyze(hfss)

    print("Q‑factor (mode 1):", result.results[1].quality_factor)
    print("Frequency  (mode 1):", result.results[1].frequency)
    ```

!!! note "Need lower‑level control?"
    [`PyaedtFileParameters`](../api/pyaedt_file_parameters.md) handles HFSS launch and clean‑up, but you can use raw PyAEDT calls if you prefer.

---

## Example 2: QuantumEPR analysis (complex design)

`QuantumEPR` post‑processes an eigenmode solution to compute χ‑matrix elements and participation ratios.

!!! info "Steps"
    1. Copy the complex bundle: `quansys example --type complex`  
    2. Solve eigenmodes as in Example 1 (same design/setup names).  
    3. Instantiate `QuantumEPR` with **mode‑to‑label** and **junction** metadata.

### Key constructor arguments

| Argument | What it does                                        | API                                          |
|----------|-----------------------------------------------------|----------------------------------------------|
| `modes_to_labels` | Map mode indices → labels e.g. `{1: "q0", 2: "r0"}` | [`ModesToLabels`](../api/modes_to_labels.md) |
| `junctions_config` | Describe Josephson junctions parameters             | [`ConfigJunction`](../api/junctions.md)      |

Full details: [`QuantumEPR` API](../api/quantum_epr.md).

### Minimal script

!!! example "quantum_epr_demo.py"
    ```python
    from quansys.simulation import EigenmodeAnalysis, QuantumEPR
    from quansys.workflow import PyaedtFileParameters
    from quansys.simulation import ConfigJunction

    params = PyaedtFileParameters(
        "complex_design.aedt",
        design_name="my_design",
        non_graphical=True
    )

    eigen = EigenmodeAnalysis("my_design", "Setup1")

    epr = QuantumEPR(
        design_name="my_design",
        setup_name="Setup1",
        modes_to_labels={1: "q0", 2: "r0", 3: "bus"},
        junctions_config=[
            ConfigJunction(
                name="transmon_junction_line",
                inductance_variable_name="junction_inductance"
            )
        ]
    )

    with params.open_pyaedt_file() as hfss:
        eigen.analyze(hfss)          # solve eigenmodes
        epr_result = epr.analyze(hfss)

    print("χ(q0‑r0):", epr_result.results["chi_q0r0"])
    print("Total  Q:", epr_result.results["Q_total"])
    ```

`QuantumEPR` reuses the eigenmode solution already stored in HFSS, so the second call is quick.  
The returned **`QuantumResults`** object offers `.flatten()` and `.model_dump()` just like classical results.

!!! tip "Advanced `ModesToLabels` tricks"
    Want automatic mode labelling? Combine **manual** and **order‑based** inferences:

    ```python  
    from quansys.simulation.quantum_epr.modes_to_labels import (  
        ModesToLabels, ManualInference, OrderInference)  

    modes_to_labels = ModesToLabels(inferences=[  
        ManualInference(mode_number=2, label="Bus"),          # pin mode 2 as ‘Bus’  
        OrderInference(                                       # then pick two highest‑Q modes …  
            num=2,                                            # … out of the remaining set  
            min_or_max="max",  
            quantity="quality_factor",  
            ordered_labels_by_frequency=["Q1", "Q2"]          # label them by freq order  
        )  
    ]) 
    ```

    The engine applies all **manual** rules first, then runs the automatic
    [`OrderInference`](../api/order_inference.md) rules on the *remaining* modes.
    
!!! warning "Mode‑count limit"
    A single QuantumEPR run can label **at most three modes**. 
    If you need five labels, split them into two runs—e.g., one QuantumEPR with modes {q0,r0,bus} and another with {q1,q2}.
---

## Access & save results

| Method                     | Returns     | Typical use      |
|----------------------------|-------------|------------------|
| `result.model_dump()`      | nested dict | full archival    |
| `result.model_dump_json()` | JSON string | logging, REST    |
| `result.flatten()`         | flat dict   | DataFrame / CSV  |

Use **`flatten()`** for aggregation; use **`model_dump()`** when you need every detail.

---

## Design philosophy

!!! abstract "Unified interface"
    1. Every simulation class implements `.analyze(hfss)` to execute.  
    2. Results are **JSON‑serializable** and provide `.flatten()`.

This consistency lets you string simulations together in larger automation pipelines.

---

## Advanced note

??? note "CPU cores"
    `EigenmodeAnalysis` exposes a `cores` attribute to control CPU allocation—handy for cluster jobs.

---
