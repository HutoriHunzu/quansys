# 🚀 Best Practices for Cluster Jobs

`quansys` is designed so that a workflow you test on your laptop will behave the same way on a large compute cluster.  
Follow the sequence below to keep every run **predictable, repeatable, and cluster-ready**.

---

## 1 · Pick the Right Builder

Choose a builder that matches how you want to create or edit the HFSS model:

| Builder | When to Use | Docs |
|---------|-------------|------|
| **DesignVariableBuilder** | You already have an `.aedt` and only need to tweak project-level variables. | [`DesignVariableBuilder`](../api/design_variable_builder.md) |
| **ModuleBuilder** | You prefer a reusable Python module to generate or modify geometry. | [`ModuleBuilder`](../api/module_builder.md) |

(See the full list in the API reference under **Builders**.)

---

## 2 · Define Everything in a Config File

Create a single YAML/TOML file containing design variables, solver options, and cluster resources.  
If it might change between runs, put it in the config—not in Python code.

---

## 3 · Test Locally

```bash
quansys run config.yaml
```

A local run confirms the builder and settings work before you consume cluster hours.

---

## 4 · Submit to the Cluster

```bash
quansys submit config.yaml my_env --name job_name
```

`submit` copies the project, packages the config, and hands off the job to the scheduler.

---

!!! tip
    *Commit the config file—and the design artefacts—to Git.*
    With code and configuration under version control, every cluster run can be traced, repeated, and trusted.

