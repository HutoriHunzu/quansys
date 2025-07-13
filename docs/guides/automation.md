# ⚙️ Automation Workflows

A **workflow** is a function that enables automated simulation runs.  
For each parameter set it passes through four phases:

| Phase     | What happens                                            | Config keys¹               |
|-----------|---------------------------------------------------------|----------------------------|
| Prepare   | Create a folder; optionally copy an existing **.AEDT**. | `prepare_folder`           |
| Build     | Modify the **.AEDT** for the current parameters.        | `builder`, `builder_sweep` |
| Simulate  | Run analyses for each sweep point.²                     | `simulations`              |
| Aggregate | Merge JSON outputs into CSV tables.                     | `aggregation_dict`         |

¹ Full field docs: [WorkflowConfig](../api/workflow_config.md)  
² Identifiers **"build"** and **"prepare"** are reserved – see details in *Simulate*.

Reruns are incremental: finished steps are skipped automatically.

---

## Quick-start

A minimal Python example using [`WorkflowConfig`](../api/workflow_config.md) and [`execute_workflow`](../api/execute_workflow.md).

!!! example "Python example"
    ```python
    from pathlib import Path
    from pyhfss import (
        WorkflowConfig, PyaedtFileParameters,
        EigenmodeAnalysis, DesignVariableBuilder, execute_workflow
    )
    from pykit.sweeper import DictSweep

    config = WorkflowConfig(
        pyaedt_file_parameters=PyaedtFileParameters(
            file_path=Path("resources/simple_design.aedt")                  # Read AEDT
        ),
        builder=DesignVariableBuilder(design_name="my_design"),             # Modify model

        builder_sweep=[DictSweep(                                           # Parameter combos
                        parameters={"chip_base_width": ["3 mm", "4 mm"]}
                        )],                                                 
        simulations={                                                       # What to run
            "classical": EigenmodeAnalysis(setup_name="Setup1",
                                           design_name="my_design")
        },
        aggregation_dict={"classical_agg": ["build", "classical"]}          # How to merge
    )

    execute_workflow(config)
    ```

**What you’ll see**

```text
results/iterations/<uid>/
├─ build/parameters.json        # {"chip_base_width": "3 mm" | "4 mm"}
└─ classical/classical.json     # simulation output

results/aggregations/classical_agg.csv   # parameters merged with results
```

!!! note
    `"build"` and `"prepare"` are reserved identifiers and therefore **cannot**
    be used as keys in `simulations`. `"build"` holds sweep parameters;
    `"prepare"` stores the path to the copied AEDT.

---


---

## Phases

### Prepare – Folders & Templates

`PrepareFolderConfig` decides whether the template **.AEDT** file is copied and what name it will have.
The user doesn't need specify anything, this is a default behavior.

```text
results/iterations/<uid>/
└─ build.aedt
```

!!! note "Copy rules"
    `copy_enabled = True` (default) – duplicate the template for each sweep.

---

### Build – Modify the Model

A **builder** receives an open HFSS session plus the current parameter dict.

| Builder type                                                 | Purpose                               |
| ------------------------------------------------------------ | ------------------------------------- |
| [`DesignVariableBuilder`](../api/design_variable_builder.md) | Set design variables                  |
| [`FunctionBuilder`](../api/function_builder.md)              | Run a user-supplied Python function   |
| [`ModuleBuilder`](../api/module_builder.md)                  | Import and execute `<module>.build()` |

!!! tip "Traceability"
    Each sweep’s parameters are saved to `build/parameters.json`.

---

### Simulate – Run Analyses

`simulations` is a `dict[str, Simulation]` (see the
[Simulations guide](simulations.md) for APIs). Keys are **identifiers** used later
for aggregation.

!!! danger "Reserved identifiers"
    Do **not** name a simulation `"build"` or `"prepare"` – those identifiers
    are reserved for internal bookkeeping.

!!! example "Simulations dict"
    ```python
        simulations = {
            "classical": EigenmodeAnalysis(setup_name="Setup1",
                                           design_name="my_design"),
            "epr": QuantumEPR(setup_name="Setup1",
                              design_name="my_design",
                              modes_to_labels={0: "q0"})
        }
    ```

Outputs are JSON files:

```text
results/iterations/<uid>/<identifier>.json
```

---

### Aggregate – Collect Results

```python
aggregation_dict = {
    "classical_agg": ["classical"],
    "combined":      ["classical", "epr"]
}
```

For each entry the engine:

1. Loads matching result files.
2. Calls `.flatten()` **to turn** nested keys into columns (see Simulations guide).
3. Writes a CSV in `results/aggregations/`.

---
