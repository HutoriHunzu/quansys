# ⚙️ Automation Workflows

A **workflow** is a function that **facilitates** automated simulation runs.  
For each parameter set it goes through:

| Phase     | What happens                                            | Config keys¹               |
|-----------|---------------------------------------------------------|----------------------------|
| Prepare   | Create a folder; optionally copy an existing **.aedt**. | `prepare_folder`           |
| Build     | Modify the **.aedt** for the current parameters.        | `builder`, `builder_sweep` |
| Simulate  | Run analyses for each sweep point.²                     | `simulations`              |
| Aggregate | Merge JSON outputs into CSV tables.                     | `aggregation_dict`         |

¹ Full field docs: [WorkflowConfig](../api/workflow_config.md)  
² Identifiers "build" and "prepare" are reserved – see Simulate.


Reruns are incremental: finished steps are skipped automatically.

---

## Quick-start

Showcasing a simple example of how to use the automation feature by instantiation of
[WorkflowConfig](../api/workflow_config.md) and using [execute_workflow](../api/execute_workflow.md).

!!! example "workflow execution from python"
    ```python
    from pathlib import Path
    from pyhfss import (WorkflowConfig, PyaedtFileParameters,
                        EigenmodeAnalysis, DesignVariableBuilder, execute_workflow)
    from pykit.sweeper import DictSweep
    
    config = WorkflowConfig(

        pyaedt_file_parameters=PyaedtFileParameters(
            file_path=Path("resources/simple_design.aedt")
        ),

        builder=DesignVariableBuilder(design_name="my_design"),

        builder_sweep=[DictSweep(parameters={"chip_base_width": ["3 mm", "4 mm"]})],

        simulations={
            "classical": EigenmodeAnalysis(setup_name="Setup1",
                                           design_name="my_design")
        },

        aggregation_dict={"classical_agg": ["build", "classical"]}
    )
    
    execute_workflow(config)
    ```

    What you’ll see:

    1. **Iteration folders** 
        ```
        results/iterations/000/ --> {"chip_base_width": "3 mm"} 
        results/iterations/001/ --> {"chip_base_width": "4 mm"}
        ```
    2. **Inside each folder**
        ```
        classical.json        --> simulation output 
        build_parameters.json –-> current parameters (i.e. {"chip_base_width": "3 mm"})
        ```

    3. **Aggregation folder**:
        ```
        results/aggregations/classical_agg.csv
        ```
        Because "build" is listed in aggregation_dict, those parameters are merged
        into classical_agg.csv.


!!! note
    The aggregation dict contains "build" as one of the identifiers. This
    is a reserved identifier and cannot be part of the simulations keys.
    It is used to load the parameters set used for each iteration to be merged
    with the simulation results. 

---


## Phases:

A breakdown of the different phases involved in the automation.

### Prepare – Folders & Templates

`PrepareFolderConfig` decides whether the template AEDT is copied.

```text
results/iterations/
└─ prepare/<uid>/simple_design.aedt
```

!!! note "Copy rules"
    **copy\_enabled =True** (default) – duplicate the template for each sweep.
    If `file_path=None`, a *builder* must create the project from scratch.

---

### Build – Modify the Model

A **builder** receives an open HFSS session plus the current parameter dict.

| Builder type                                                  | Purpose                               |
|---------------------------------------------------------------|---------------------------------------|
| [`DesignVariableBuilder`](../api/design_variable_builder.md)  | Set design variables                  |
| [`FunctionBuilder`](../api/function_builder.md)               | Run arbitrary Python                  |
| [`ModuleBuilder`](../api/module_builder.md)                   | Import `<module>.build()` at runtime  |


!!! tip "Traceability"
    Each sweep’s parameters are saved to `build/parameters.json`.

---

### Simulate – Run Analyses

`simulations` is a `#!py3 dict[str, Simulation]` where the values are simulation instances (see the [Simulations](simulations.md) guide for further information).
and the keys are called **identifiers**. 
They are used to keep track on the different simulations we execute. These identifiers are later used 
for aggregation purposes. 

!!! danger "Reserved name"
    The following names are reserved identifiers and cannot be used for naming a simulation:

    - `#!py3 'build'`   - builder phase, used for merging parameters to the results)
    - `#!py3 'prepare'` - preparation phase, used for storing AEDT path

    Do **not** use any of these names as an identifier.

!!! example "simulations example"

    ```python
    simulations = {
        "classical": EigenmodeAnalysis(setup_name="Setup1",
                                       design_name="my_design"),
        "epr": QuantumEpr(setup_name="Setup1",
                          design_name="my_design",
                          modes_to_labels={0: "q0"})
    }
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
2. Calls `.flatten()` so nested keys become columns (see Simulations Guide for details).
3. Writes a CSV in `results/aggregations/`.

---

## `WorkflowConfig` cheat-sheet

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

Use `.save_to_yaml()` / `.load_from_yaml()` for fully reproducible runs.

---
