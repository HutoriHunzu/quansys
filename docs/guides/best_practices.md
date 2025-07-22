# 🚀 Best Practices for Local & Cluster Runs

A workflow you test on your laptop should behave **identically** on a large compute cluster.  
Follow the checklist below to keep every run predictable, resumable, and version‑controlled.

---

## 1 Choose the right builder

| Builder                    | When to use                                                            | Docs                                                          |
|----------------------------|------------------------------------------------------------------------|---------------------------------------------------------------|
| **DesignVariableBuilder* * | You have an existing `.aedt` and only need to tweak design variables.  | [`DesignVariableBuilder`](../api/design_variable_builder.md)  |
| **ModuleBuilder**          | You want a reusable Python module to generate/modify geometry.         | [`ModuleBuilder`](../api/module_builder.md)                   |

*(See all builders in the API reference.)*

---

## 2 Put everything in a `WorkflowConfig`

* Create or load a `WorkflowConfig` in Python **or** YAML.  
* Include solver options, sweep parameters, simulation list, and cluster resources.  
* **Avoid hard‑coding** these values in ad‑hoc Python scripts.

Reserved identifiers: **`build`** and **`prepare`** — never use them as simulation names.

---

## 3 Test locally first

intro bash  
quansys run config.yaml  

A local run confirms the builder works and the sweep hashes create the expected UID folders (`000`, `001`, …).

---

## 4 Submit to the cluster

intro bash  
quansys submit config.yaml my_env --name job_name  

`submit` packages the project, stages input files, and hands the job to the scheduler.

---

## 5 Version‑control the artefacts

!!! tip
    Commit the **config file** and the **template design** (`template.aedt`) to Git.  
    With code *and* configuration under version control, every cluster run can be traced, repeated, and trusted.

---

### YAML round‑trip snippet

Need to tweak the workflow in CI without touching Python code?

```python  
from quansys import WorkflowConfig, execute_workflow  

cfg = WorkflowConfig.load_from_yaml("config.yaml")  
cfg.pyaedt_file_parameters.non_graphical = False      # optional tweak  
execute_workflow(cfg)
```  

Use `cfg.save_to_yaml("new_config.yaml")` to persist edits back to disk.
