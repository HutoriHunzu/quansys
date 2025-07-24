# 🖥️ Terminal Guide: Complete CLI Reference

The **quansys CLI** provides fast, intuitive commands for managing simulation workflows—from quick local testing to large-scale cluster submissions.

## Quick Start

```bash
# Get help for any command
quansys --help
quansys run --help

# Copy example files to get started
quansys example --list
quansys example --type simple

# Test your workflow locally
quansys run simple_config.yaml

# Submit to cluster
quansys submit simple_config.yaml my_env --name test_job
```

---

## Commands Overview

| Command | Purpose | Use Case |
|---------|---------|----------|
| `quansys run` | Execute workflow locally | Testing, debugging, small sweeps |
| `quansys submit` | Submit to cluster scheduler | Large parameter sweeps, production runs |
| `quansys example` | Copy example files | Getting started, templates |

---

## `quansys run` - Local Execution

**Execute a workflow on your local machine.**

### Basic Usage
```bash
quansys run config.yaml
```

### What It Does
1. Loads your `config.yaml` workflow configuration
2. Creates result folders (`results/iterations/000/`, `001/`, etc.)
3. Runs all simulations for each parameter combination
4. Generates CSV aggregation files in `results/aggregations/`

### When to Use
- **Development**: Test your builder and sweep parameters
- **Debugging**: Validate AEDT files and simulation settings  
- **Small jobs**: Quick parameter sweeps that finish in minutes
- **Prototyping**: Iterate on workflow design before cluster submission

### Performance Tips
- Use `non_graphical: true` in your config for faster headless execution
- Start with small parameter sweeps to validate your setup
- Check `results/iterations/000/build_parameters.json` to verify parameter application

### Example Workflow
```bash
# 1. Copy example files
quansys example --type simple

# 2. Edit simple_config.yaml as needed

# 3. Test locally
quansys run simple_config.yaml

# 4. Check results
ls results/aggregations/
```

---

## `quansys submit` - Cluster Submission

**Package and submit workflows to cluster schedulers (LSF, SLURM, etc.).**

### Basic Usage
```bash
quansys submit config.yaml ENV_NAME --name JOB_NAME [OPTIONS]
```

### Required Arguments
- `config.yaml` - Your workflow configuration file
- `ENV_NAME` - Conda environment name available on the cluster
- `--name JOB_NAME` - Unique name for this job (creates folder)

### Common Options
```bash
--files FILE1 FILE2     # Copy additional files to job folder
--mem 120000            # Total memory in MB (default: 120GB)
--timeout 03:00         # Job duration in HH:MM format
--prepare               # Only prepare job folder, don't submit
--overwrite             # Replace existing job folder
```

### Complete Example
```bash
quansys submit my_config.yaml quantum_env \
  --name transmon_sweep \
  --files custom_design.aedt helper_script.py \
  --mem 160000 \
  --timeout 08:00
```

### What It Creates
```
transmon_sweep/
├── config.yaml              # Your workflow config
├── custom_design.aedt       # Copied input files
├── helper_script.py         # Additional files
├── job_submission.sh        # Scheduler script (bsub/sbatch)
└── simulation_script.sh     # Execution script
```

### Workflow Process
1. **Prepare**: Creates job folder, copies files, generates scripts
2. **Submit**: Executes `job_submission.sh` to queue the job
3. **Execute**: Cluster runs `simulation_script.sh` when resources available
4. **Results**: Output appears in job folder when complete

### Cluster Configuration
The generated `job_submission.sh` automatically:
- Requests appropriate CPU cores (from `cores` in simulation configs)
- Sets memory limits per core
- Loads ANSYS modules and activates your conda environment
- Handles job scheduling and error logging

---

## 📁 `quansys example` - Example Files

**Copy template files and configurations to get started quickly.**

### List Available Examples
```bash
quansys example --list
```
**Output:**
```
Available example types:
  - simple   : minimal AEDT and config for basic sweep
  - complex  : larger AEDT and config with multiple analyses
```

### Copy Example Files
```bash
# Copy both AEDT and config files (default)
quansys example --type simple

# Copy only AEDT file
quansys example --type complex --no-config

# Equivalent to:
quansys example --type simple --with-config
```

### What You Get

**Simple Example:**
- `simple_design.aedt` - Basic resonator design
- `simple_config.yaml` - Single eigenmode analysis with parameter sweep

**Complex Example:**  
- `complex_design.aedt` - Multi-component quantum device
- `complex_config.yaml` - Multiple analyses, junctions, advanced sweeps

### Using Examples
```bash
# 1. Get simple example
quansys example --type simple

# 2. Customize the config
# Edit simple_config.yaml to match your needs

# 3. Test locally
quansys run simple_config.yaml

# 4. Submit to cluster
quansys submit simple_config.yaml my_env --name my_first_job
```

---

## 💡 Best Practices

### 🔍 Before You Start
- Always run `quansys example --list` to see available templates
- Use `--help` with any command to see all options
- Test workflows locally with `run` before cluster `submit`

### 🧪 Development Workflow
```bash
# 1. Start with examples
quansys example --type simple

# 2. Iterate locally
quansys run simple_config.yaml
# Edit config, repeat until satisfied

# 3. Scale to cluster
quansys submit simple_config.yaml prod_env --name production_sweep
```

### 📊 Managing Results
- **Local runs**: Results in `results/` folder in current directory
- **Cluster jobs**: Results in job folder (`JOB_NAME/results/`)
- **CSV files**: Check `aggregations/` folder for flattened data
- **Raw data**: Individual results in `iterations/NNN/` folders

### 🔧 Configuration Tips
- Keep separate config files for different experiments
- Use descriptive job names (`--name transmon_freq_sweep` not `--name test`)
- Start with small parameter ranges before large sweeps
- Version control your config files with Git

### ⚡ Performance Notes
- CLI startup is optimized - simple commands like `--help` are instant  
- Heavy imports only load when actually running simulations
- Use `--prepare` to validate job setup without submitting

---

## 🔍 Troubleshooting

### Command Not Found
```bash
# Ensure quansys is installed
pip install -e .

# Check installation
quansys --help
```

### Slow CLI Performance
The CLI is optimized for fast startup. If you experience slowness:
- Simple commands (`--help`, `example --list`) should be instant
- Only heavy simulation commands load full dependencies  
- Check your conda environment setup

### Job Submission Issues
```bash
# Test job preparation without submitting
quansys submit config.yaml env_name --name test --prepare

# Check generated scripts
cat test/job_submission.sh
cat test/simulation_script.sh
```

### Configuration Errors
- Validate YAML syntax in your config file
- Ensure AEDT file paths are correct
- Check conda environment exists on cluster
- Verify file permissions for cluster access

---

## 🎯 Related Documentation

- **[Workflow Configuration](automation.md)** - Understanding config.yaml structure
- **[Simulation Guide](simulations.md)** - Available analysis types  
- **[Best Practices](best_practices.md)** - Production workflow tips
