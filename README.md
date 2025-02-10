# pysubmit

pysubmit is a Python package designed for automating HFSS simulations by migrating pyepr to use pyaedt instead of COM, automating parameter scans via customizable workflows, and providing a CLI for cluster execution.

## Overview

pysubmit serves three primary functions:
1. **API Migration:**  
   Migrates the pyepr package to leverage pyaedt for HFSS simulations.
2. **Automated Workflows:**  
   Automates simulation parameter scans and workflow management with customizable builders and sweep configurations.
3. **Command Line Interface (CLI):**  
   Provides CLI commands to prepare, submit, rerun, and execute simulation workflows on a cluster.

## Features

- **Simulation Module:**  
  Supports classical HFSS simulations and advanced energy participation ratio (EPR) analysis for quantum parameter extraction.
  
- **Workflow Module:**  
  Enables automated simulation setups with builder configurations, session management, and parameter sweeps.
  
- **CLI Interface:**  
  Built using Typer for an intuitive command-line experience. Key commands include:
  - `submit`: Prepare and optionally submit a simulation job.
  - `rerun`: Re-run a simulation job from an existing project.
  - `run_flow`: Execute the complete workflow as defined in a configuration file.

## Installation

Install pysubmit via pip:

```bash
git clone https://github.com/RosenblumLab/pysubmit.git
pip install <path_to_pysubmit_repo>
