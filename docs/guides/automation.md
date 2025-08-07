# ⚙️ Automation Workflows

A **workflow** is a repeatable four‑phase loop that quansys drives for each unique sweep point:

| Phase         | What happens                                                       | Key `WorkflowConfig` fields |
|---------------|--------------------------------------------------------------------|-----------------------------|
| **Prepare**   | Make an iteration folder, optionally copy a fresh template`.aedt`  | `prepare_folder`            |
| **Build**     | Edit the project for the current parameters                        | `builder`, `builder_sweep`  |
| **Simulate**  | Run one or more `Simulation` objects                               | `simulations`               |
| **Aggregate** | Flatten JSON results and write CSVs                                | `aggregation_dict`          |

!!! tip "Stateful & resumable"

    quansys **hashes every sweep dict** (e.g. `{"chip_base_width": "3 mm"}`) and keeps a ledger of completed phases.  
    - If the hash is **new**, it allocates the next zero‑padded UID folder (`000`,`001`, …).  
    - If the hash **matches** a previous run, the engine skips the entire sweep—or resumes at the first unfinished phase.

!!! tip "Reserved identifier: `build`"

    - quansys automatically writes **`build_parameters.json`** inside every UID folder.  
    - The identifier for those parameters is hard‑coded as **`build`**.  
    - Therefore: never name a simulation `"build"` or `"prepare"`, but **do** use `"build"` when you want the parameter columns in `aggregation_dict`.


---

## Quick‑start (Python)

Below is a minimal workflow in **pure Python**.
For this example we need a working AEDT, we'll use the `simple_design.aedt` (refer to [Getting Started](../getting_started.md) for more information)
For demo purposes we sweep `chip_base_width` over `"3mm"` and `"3.5mm"`.

```python  
from pathlib import Path
from quansys.workflow import (
    WorkflowConfig, PyaedtFileParameters, 
    DesignVariableBuilder, execute_workflow
)
from quansys.simulation import EigenmodeAnalysis
from pycaddy.sweeper import DictSweep

cfg = WorkflowConfig(
    pyaedt_file_parameters=PyaedtFileParameters(
        file_path=Path("simple_design.aedt")),

    builder=DesignVariableBuilder(design_name="my_design"),
    
    builder_sweep=[DictSweep(parameters={
        "resonator_length": ["3mm", "3.5mm"],
    })],

    simulations={
        "eigenmode": EigenmodeAnalysis(design_name="my_design", 
                                       setup_name="Setup1")
    },

    aggregation_dict={
        "results": ["build", "eigenmode"]
    }
)


execute_workflow(cfg)  

```

---

### Folder layout

```text  
results/  
├─ iterations/  
│├─ 000/   # chip_base_width 3mm  
││├─ build.aedt  
││├─ build_parameters.json  
││└─ eigenmode.json  
│└─ 001/   # chip_base_width 3.5mm  
│├─ …  
└─ aggregations/  
└─ results.csv  

```

Re‑running the script creates **002**, **003**, … only for *new* parameter hashes.

### Transmon + Resonator Example

For quantum analysis with junction coupling we'll need a more complex AEDT file. For this demo we'll use the `complex_design.aedt`
file (refer to [Getting Started](../getting_started.md) for more information)

```python
from pathlib import Path
from quansys.simulation import (QuantumEPR, ConfigJunction, 
                                EigenmodeAnalysis)
from quansys.workflow import (
    WorkflowConfig, PyaedtFileParameters, 
    DesignVariableBuilder, execute_workflow
)
from quansys.simulation import 
from pycaddy.sweeper import DictSweep

cfg = WorkflowConfig(
    pyaedt_file_parameters=PyaedtFileParameters
    (file_path=Path("complex_design.aedt")),

    builder=DesignVariableBuilder(design_name="my_design"),
    builder_sweep=[DictSweep(parameters={
        "junction_inductance": ["10nh", "11nh"],
    })],

    simulations={
        "eigenmode": EigenmodeAnalysis(design_name="my_design", 
                                       setup_name="Setup1"),
        "quantum": QuantumEPR(
            design_name="my_design",
            setup_name="Setup1",
            modes_to_labels={1: "transmon", 2: "readout"},
            junctions_infos=[ConfigJunction(
                line_name="transmon_junction_line",
                inductance_variable_name="junction_inductance"
            )]
        )
    },

    aggregation_dict={
        "eigenmode_results": ["build", "eigenmode"],
        "quantum_results": ["build", "quantum"]
    }
)

execute_workflow(cfg)

```

---

## Phase details

### 1 Prepare

*Default*: copy AEDT file into each UID folder.  

### 2 Build

| Builder                  | Goal                              | Docs                                                         |
|--------------------------|-----------------------------------|--------------------------------------------------------------|
| `DesignVariableBuilder`  | Set HFSS design variables         | [`DesignVariableBuilder`](../api/design_variable_builder.md) |
| `FunctionBuilder`        | Execute an inline Python callable | [`FunctionBuilder`](../api/function_builder.md)              |
| `ModuleBuilder`          | Import & call `<module>.build()`  | [`ModuleBuilder`](../api/module_builder.md)                  |

Each sweep’s parameters are recorded in `build_parameters.json`.

### 3 Simulate

`simulations` is a **dict** that maps *identifier → Simulation instance*.  
Identifiers must be unique and **must not** be `"build"` or `"prepare"`.


!!! warning "QuantumEPR label cap"
    A single `QuantumEPR` can label **at most three modes**.  
    Need more? Create additional entries, each with up to three labels:

    ```python  
    simulations.update({  
        "epr_set1": QuantumEPR(..., modes_to_labels={1: "q0", 2: "r0", 3: "bus"}),  
        "epr_set2": QuantumEPR(..., modes_to_labels={4: "q1", 5: "q2"})  
    })
    ```

### 4 Aggregate

Each CSV listed in `aggregation_dict` becomes a merged table—`build` columns first, followed by flattened result columns.

---

## YAML workflows (no‑code option)

A declarative **`workflow.yaml`** gives you the same power without rebuilding the config in Python—perfect for CLI runs or CI pipelines.

### 1 Save your current workflow to YAML

!!! example "Save workflow"
    ```python  
    # cfg is the Python WorkflowConfig we created above  
    cfg.save_to_yaml("complex_config.yaml")   # writes a self‑contained YAML file
    ```

### 2 Load the YAML later and execute

!!! example "Load & run"
    ```python  
    from quansys.workflow import WorkflowConfig, execute_workflow  

    cfg = WorkflowConfig.load_from_yaml("complex_config.yaml")  
    cfg.pyaedt_file_parameters.non_graphical = False   # tweak if desired  
    execute_workflow(cfg)
    ```


You can now **hand‑edit `complex_config.yaml`**—add new sweep ranges, change builders, or swap simulations—then re‑run the three‑line loader above.


---

## CLI Execution

Once you have a YAML workflow file, you can execute it directly from the command line:

- **Local testing**: `quansys run config.yaml`
- **Cluster submission**: `quansys submit config.yaml env_name --name job_name`

See the [terminal guide](terminal.md) for complete CLI examples and [best practices](best_practices.md) for workflow optimization tips.

!!! tip "Typical usage pattern"
    Most workflows use `quansys run` on a PC for local testing and `quansys submit` on Linux endpoints for cluster execution.

---

For advanced options—custom output paths, parallel workers, logging hooks—see the [`execute_workflow` API](../api/execute_workflow.md).
