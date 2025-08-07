# 📦 Installation Guide

## 1 Prerequisites

!!! info "Required software"
    * **ANSYS Electronics Desktop 2024 R2** – to open `.aedt` projects  
    * **Python≥3.11** with `pip` (or **uv**) available  
    * Windows 10/11 or a Linux workstation that can run HFSS in non‑graphical mode

---

## 2 Install quansys

```bash
pip install quansys          # standard pip
```

!!! note "Prefer uv?"
    If you use [uv](https://github.com/astral-sh/uv) for faster installs:
    ```bash
    uv pip install quansys
    ```

## 3 Packages pulled in automatically

- [PyAEDT](https://github.com/ansys/pyaedt) – Python bridge to HFSS 
- [pycaddy](https://pypi.org/project/pycaddy/) – utilities for sweeping and safe data handling
(See the [Automation](guides/automation.md) for how pycaddy is used.)

No manual installation is needed for these; `pip install quansys` brings them along.

---
Next stop: ⚡ [Quick‑Start Example Files](getting_started.md) to grab your first design.