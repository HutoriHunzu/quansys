# Automation Guide

This guide explains how to automate parameter sweeps and simulation runs using the `WorkflowConfig` class and the `execute_workflow()` function.

The workflow system lets you define reusable experiments that sweep over variables, run multiple simulations, and optionally aggregate the results into structured data.

---

## Workflow at a Glance

The `execute_workflow()` function drives the automation through four distinct phases:

1. **Preparation**: Set up working folders and optionally copy a base `.aedt` file.
2. **Model Building**: Apply parameterized modifications via a builder (e.g., design variables).
3. **Simulations**: For each sweep iteration, run the configured simulations.
4. **Aggregation**: Flatten and merge results into tabular format (e.g., CSV files).

Each run is reproducible, isolated, and cached.

---

## Running a Workflow in Python

The most straightforward way to define and execute a workflow is programmatically.

!!! example "Python-based Workflow Example"
    ```python
    from pyhfss import (
        WorkflowConfig,
        PyaedtFileParameters,
        EigenmodeAnalysis,
        DesignVariableBuilder,
        execute_workflow
    )
    from pykit.sweeper import DictSweep
    from pathlib import Path

    SIMPLE_DESIGN_AEDT = Path("resources/simple_design.aedt")

    config = WorkflowConfig(
        pyaedt_file_parameters=PyaedtFileParameters(file_path=SIMPLE_DESIGN_AEDT),

        simulations={
            "classical": EigenmodeAnalysis(
                setup_name="Setup1",
                design_name="my_design"
            )
        },

        builder=DesignVariableBuilder(design_name="my_design"),

        builder_sweep=[
            DictSweep(parameters={"chip_base_width": ["3mm", "4mm"]})
        ],

        aggregation_dict={
            "classical_agg": ["classical"]
        }
    )

    execute_workflow(config)
    ```

This configuration will:

- Sweep over two values of `chip_base_width`
- Modify the HFSS model using a `DesignVariableBuilder`
- Run a single simulation (`"classical"`) for each parameter set
- Save simulation results and aggregate them into `results/aggregations/classical_agg.csv`

---

## Phase 1: Preparation (Folder Setup)

Each workflow iteration creates an isolated folder structure to ensure reproducibility and avoid side effects. This step optionally copies a base `.aedt` file into the working folder for each parameter set.

The behavior is configured using the `prepare_folder` section of `WorkflowConfig`, which internally uses `PrepareFolderConfig`.

!!! note "File Copy Behavior"
    - If `copy_enabled` is `True` (default), the base `.aedt` file will be duplicated per run.
    - If no template is provided, the builder must be capable of creating the design from scratch.

Each prepared file lives under:  
`results/iterations/prepare/<uid>/simple_design.aedt`

---

## Phase 2: AEDT File Handling

Interaction with HFSS projects is managed through the `PyaedtFileParameters` model. This object encapsulates how `.aedt` files are opened, including:

- File path
- Version to use
- Whether to use graphical or non-graphical mode
- License options (if needed)

!!! example "Basic AEDT File Parameters"
    ```python
    PyaedtFileParameters(
        file_path="resources/simple_design.aedt",
        non_graphical=True
    )
    ```

!!! tip
    This model is passed through all phases and can be duplicated or updated with `.model_copy(update=...)`.

Each simulation, builder, and aggregation phase works with this model to safely manage HFSS sessions.

If `file_path` points to a real `.aedt` file, it will be opened or copied. If omitted, the builder is expected to create a valid project from scratch.

---
## Phase 3: Model Building (Builder Phase)

Before running simulations, the workflow can optionally modify the HFSS model based on the current parameter set. This is handled by a **builder**, which is applied during the "build" stage.

A builder receives:

- An open HFSS session (from the prepared `.aedt` file)
- The current sweep parameters as a dictionary

The builder modifies the design — for example, by setting design variables, executing scripts, or programmatically constructing geometry.

### Supported Builder Types

- `DesignVariableBuilder`: Sets HFSS design variables like `width = "3mm"`
- `FunctionBuilder`: Runs a user-defined function to modify the design
- `ModuleBuilder`: Dynamically imports a Python module and runs its logic

!!! example "DesignVariableBuilder"
    ```python
    DesignVariableBuilder(
        design_name="my_design"
    )
    ```

!!! note
    Builders are **optional**. If omitted, the existing design is used as-is.  
    If no `.aedt` file is provided, a builder is **required** to create the project structure.

During this phase, the current sweep parameters are also saved to `parameters.json` under the `build` session folder.

---

## Phase 4: Simulations

Once the design is ready, the workflow runs one or more simulations, defined in the `simulations` dictionary of `WorkflowConfig`.

Each entry is a key-value pair:

- Key = **identifier** (used for output and aggregation)
- Value = A configured simulation object (e.g., `EigenmodeAnalysis`, `QuantumEpr`)

These simulations are executed per sweep point, one after the other.

!!! example "Simulations Dictionary"
    ```python
    simulations = {
        "classical": EigenmodeAnalysis(
            setup_name="Setup1",
            design_name="my_design"
        ),
        "epr": QuantumEpr(
            setup_name="Setup1",
            design_name="my_design",
            modes_to_labels={0: "q0"},
            junctions_infos=[...]
        )
    }
    ```

Each simulation must define a `.design_name`, which determines the HFSS design to activate within the `.aedt` file.

The result of each simulation:

- Is computed using `.analyze(hfss)`
- Must be **JSON-serializable**
- Is saved to disk as a `.json` file under `results/iterations/<identifier>/`

!!! alert "Reserved Identifiers"
    The identifier `"build"` is reserved for internal use (e.g., for storing parameter sets).  
    Do not use `"build"` as a simulation name in your config.

---
## Phase 5: Aggregation

After all simulations are complete, the workflow can optionally **aggregate** results across sweep iterations.

This is defined by the `aggregation_dict` field in `WorkflowConfig`. It maps output names to lists of simulation identifiers.

!!! example "Aggregation Configuration"
    ```python
    aggregation_dict = {
        "classical_agg": ["classical"],
        "combined": ["classical", "epr"]
    }
    ```

For each entry:

- The workflow gathers all matching results by identifier
- Results are flattened using `.flatten()` (to ensure a table-like structure)
- A `.csv` file is written to `results/aggregations/<name>.csv`

Each row corresponds to one parameter set. Columns come from the flattened result keys.

---

### Example Aggregated Output

If your simulation returns structured results like this:

```json
{
  "frequencies": [5.1, 5.4],
  "quality_factors": [10000, 9500],
  "parameters": {"chip_base_width": "3mm"}
}
```

Then the flattened form may look like:

```json
{
  "frequencies.0": 5.1,
  "frequencies.1": 5.4,
  "quality_factors.0": 10000,
  "quality_factors.1": 9500,
  "parameters.chip_base_width": "3mm"
}
```

This format is suitable for tabular tools like **pandas**, spreadsheets, or databases.

---

### Output Location

All aggregated files are saved under:

```text
results/aggregations/
├── classical_agg.csv
└── combined.csv
```

!!! warning "Flattening Drops Structure"
The `.flatten()` method simplifies the data and removes nested structure.
Use it only for aggregation — to persist full results, use `.model_dump()` or `.model_dump_json()`.

---
