
# Automation Workflows

Design once – sweep, simulate, and aggregate forever.  
A workflow is a repeatable script that:

1. Copies or creates an HFSS project.
2. Tweaks it per parameter set.
3. Runs one or more simulations.
4. Flattens the results into tidy CSV files.

Everything is reproducible and cached, so reruns skip what’s already done.

---

## Quick-start (Python)

```python
from pathlib import Path
from pyhfss import (
    WorkflowConfig, PyaedtFileParameters,
    EigenmodeAnalysis, DesignVariableBuilder, execute_workflow
)
from pykit.sweeper import DictSweep

config = WorkflowConfig(
    pyaedt_file_parameters=PyaedtFileParameters(
        file_path=Path("resources/simple_design.aedt"), non_graphical=True
    ),
    builder=DesignVariableBuilder(design_name="my_design"),
    builder_sweep=[DictSweep(parameters={"chip_base_width": ["3 mm", "4 mm"]})],
    simulations={
        "classical": EigenmodeAnalysis(setup_name="Setup1", design_name="my_design")
    },
    aggregation_dict={"classical_agg": ["classical"]}
)

execute_workflow(config)
```

*Runs 2 sweeps × 1 simulation → `results/aggregations/classical_agg.csv`.*

---

## Life-cycle

```text
prepare  →  build  →  simulate  →  aggregate
```

| Phase     | What happens                                     | Key config fields          |
| --------- | ------------------------------------------------ | -------------------------- |
| Prepare   | Create folder, optionally copy template `.aedt`. | `prepare_folder`           |
| Build     | Modify project according to current parameters.  | `builder`, `builder_sweep` |
| Simulate  | Run one or more analyses per sweep point.        | `simulations`              |
| Aggregate | Merge JSON outputs into CSV tables.              | `aggregation_dict`         |

---

## 1. Prepare – Folders & Templates

`PrepareFolderConfig` controls if/where a template file is copied.

```text
results/iterations/
└─ prepare/<uid>/simple_design.aedt
```

!!! note "Copy rules"
    **copy\_enabled =True** (default) – duplicate the template for every sweep point.
    If no template is given (`file_path=None`), a *builder* must create the project from scratch.

---

## 2. Build – Modify the Model

A **builder** receives an open HFSS session and the current parameter dict.

Supported builders:

| Type                    | Purpose                                      |
| ----------------------- | -------------------------------------------- |
| `DesignVariableBuilder` | Set HFSS design variables (`width = "3 mm"`) |
| `FunctionBuilder`       | Call a user-supplied Python function         |
| `ModuleBuilder`         | Import a module’s `build()` at runtime       |

!!! tip "Parameters on disk"
    Every sweep’s parameters are saved to `build/parameters.json` for traceability.

---

## 3. Simulate – Run Analyses

The type of `simulations` is a `#!py3 dict[str, Simulation]`.
The *key* is an identifier; the *value* is a configured analysis object (e.g., [EigenmodeAnalysis](../api/eigenmode_analysis.md), 
[QuantumEpr](../api/quantum_epr.md)).

```python
simulations = {
    "classical": EigenmodeAnalysis(setup_name="Setup1", 
                                   design_name="my_design"),    
    "epr": QuantumEpr(setup_name="Setup1", 
                      design_name="my_design", 
                      modes_to_labels={0: "q0"})
}
```

Results must be **JSON-serialisable**. Each run lands here:

```text
results/iterations/<identifier>/<uid>.json
```

!!! danger "Reserved name"
    Do **not** use `"build"` as a simulation identifier—it’s reserved for internal bookkeeping.

---

## 4. Aggregate – Collect Results

Map output names to lists of identifiers:

```python
aggregation_dict = {
    "classical_agg": ["classical"],
    "combined":      ["classical", "epr"]
}
```

For each entry the engine:

1. Loads the matching JSON files.
2. Calls `.flatten()` so nested dicts become column names.
3. Writes a CSV under `results/aggregations/`.

!!! warning "Flattening is lossy"
    Use `.model_dump()` if you need the original nested structure.

---

## Flattening example

Input (per sweep):

```json
{
  "frequencies": [5.1, 5.4],
  "quality_factors": [10000, 9500],
  "parameters": {"chip_base_width": "3 mm"}
}
```

Flattened row:

```json
{
  "frequencies.0": 5.1,
  "frequencies.1": 5.4,
  "quality_factors.0": 10000,
  "quality_factors.1": 9500,
  "parameters.chip_base_width": "3 mm"
}
```

Ready for **pandas**, spreadsheets, or databases.

---

## Reference – `WorkflowConfig` cheat-sheet

```yaml
root_folder: results              # Where everything is written
pyaedt_file_parameters: …         # How to open HFSS
builder: DesignVariableBuilder …  # Optional – modifies the model
builder_sweep:                    # Optional – parameter combinations
  - DictSweep: {chip_base_width: ["3 mm", "4 mm"]}
simulations:                      # One or more analyses
  classical:
    type: EigenmodeAnalysis
    setup_name: Setup1
    design_name: my_design
aggregation_dict:                 # Optional – merge CSVs
  classical_agg: ["classical"]
prepare_folder: …                 # Folder/template rules
```

Save it with `.save_to_yaml()` or load with `.load_from_yaml()` when you need fully reproducible runs.

---
