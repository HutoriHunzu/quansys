# 🖥️ Terminal Guide

The **quansys CLI** provides three main commands for managing simulation workflows.

## Commands

```bash
quansys run       # Execute workflow locally  
quansys submit    # Submit workflow to cluster
quansys example   # Copy example files
```

Use `--help` with any command to see all options:
```bash
quansys --help
quansys run --help
quansys submit --help
```

## Quick Examples

**Local workflow execution:**
```bash
quansys example --type simple
quansys run simple_config.yaml
```

**Cluster submission:**
```bash
quansys submit my_config.yaml my_env --name job_name
```