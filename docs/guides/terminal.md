# 🖥️ Command‑Line Usage Guide

The **`quansys` CLI** lets you run or submit a workflow defined in **one YAML file**—no Python coding required.

Primary commands:

| Command          | Purpose                                                |
|------------------|--------------------------------------------------------|
| `quansys run`    | Execute the workflow locally                           |
| `quansys submit` | Package and submit the workflow to a cluster scheduler |

Both commands read a `config.yaml` produced by:

- the Quick‑Start bundles (`simple_config.yaml`, `complex_config.yaml`), or  
- `cfg.save_to_yaml("config.yaml")` in Python.

!!! tip "Discover flags"

    ```bash  
    quansys run --help  
    quansys submit --help
    ```

---

## Local execution — `run`

```bash  
quansys run config.yaml  
```

Typical uses:

- Validate your builder and sweep locally.  
- Debug a new set of solver parameters.

!!! tip

    Keep separate config files for separate designs or sweeps:

    ```bash  
    quansys run configs/scan_over_inductance.yaml  
    quansys run configs/scan_over_transmon_cavity_gap.yaml
    ```

---

## Cluster submission — `submit`

```bash  
quansys submit config.yaml my_env --name batch_run --files my_design.aedt --mem 160000 --timeout 06:00
```  

Resulting folder layout:

``` text  
job_name/  
├─ config.yaml  
├─ [copied input files]  
├─ simulate.sh         # activates my_env + runs quansys run config.yaml  
└─ job_submission.sh   # the scheduler script (e.g. bsub)
```  

!!! note

    - `my_env` must be a Conda environment available on the cluster.  
    - CPU count is controlled by the `cores` field inside each `Simulation` config.

---

## Related guides

* [Automation Workflows](automation.md) — internal workflow engine  
* [Simulation Guide](simulations.md) — available simulation classes  
* [`WorkflowConfig` API](../api/workflow_config.md) — full YAML schema
