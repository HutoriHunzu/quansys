# 📦 Installation Guide

## Requirements

Ensure you have Python 3.11 or higher installed. 

!!! note "Included in the package"
    The two non-trivial packages that are installed automatically when you install `quansys`:

    - [pyaedt](https://github.com/ansys/pyaedt) - used **for interacting** with HFSS
    - [pykit](https://github.com/HutoriHunzu/pykit.git) - used **for** automation and safe data manipulation (see [Automation](guides/automation.md))
    

## Clone and Install

Clone the repository from [https://github.com/hutorihunzu/quansys.git](https://github.com/hutorihunzu/quansys.git)
to your local machine and install the pacakge using pip:
```bash
git clone https://github.com/hutorihunzu/quansys.git
pip install -e <PATH_TO_QUANSYS>
```

!!! note "Using uv"
    If you have [`uv`](https://github.com/astral-sh/uv) installed, you can use:
    ```bash
    uv pip install -e <PATH_TO_QUANSYS>
    ```




