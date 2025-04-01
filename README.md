# KPoints Generator

A Python package that wraps around the Java-based k-point grid generator for VASP calculations.

## Installation

```bash
pip install kpoints-generator
```

### Prerequisites

- Python 3.6+
- Java Runtime Environment (JRE)

## Usage

### Python API

```python
import kpoints_generator as kpg

# Check if all prerequisites are met
success, message = kpg.check_prerequisites()
if not success:
    print(f"Warning: {message}")

# Generate a KPOINTS file in the current directory
kpoints_file = kpg.generate_kpoints(
    mindistance=0.2,  # Required parameter
    vasp_directory="./my_vasp_calculation",  # Optional, defaults to current dir
    precalc_params={  # Optional additional parameters for PRECALC
        "WRITE_LATTICE_VECTORS": "True",
        "HEADER" : "VERBOSE",
        "INCLUDEGAMMA" : "AUTO",
    },
    output_file="KPOINTS",  # Optional, defaults to "KPOINTS"
)

print(f"Created KPOINTS file at: {kpoints_file}")
```

### Command Line Interface

The package also provides a command-line interface:

```bash
# Generate a KPOINTS file with mindistance=0.2
kpoints-generator --mindistance 0.2

# Specify a different directory
kpoints-generator --mindistance 0.2 --directory ./my_vasp_calculation

# Check if prerequisites are met without generating k-points
kpoints-generator --check
```

## Advanced Usage

### Custom PRECALC Parameters

You can specify additional parameters for the PRECALC file:

```python
kpg.generate_kpoints(
    mindistance=0.2,
    precalc_params={
        "GAMMA": "TRUE",
        "EVENK": "TRUE",
        "KPPRA": "1000"
    }
)
```

## PRECALC Configuration

The package includes a [PRECALC_template](PRECALC_template) file in the root directory that lists all available configuration options. You can use this as a reference when setting parameters for k-point grid generation.

The basic required parameter is `MINDISTANCE`, but many other options are available for fine-tuning the grid.

### Command-line PRECALC Parameters

You can specify additional parameters for the PRECALC file through the command line:

```bash
kpoints-generator --mindistance 0.2 --precalc-param "GAMMA=TRUE" --precalc-param "EVENK=TRUE"
```

## How It Works

This package bundles the Java-based k-point grid generator and provides a Python interface to it. Under the hood, it:

1. Creates a temporary directory
2. Copies the necessary VASP input files
3. Creates a PRECALC file with the specified parameters
4. Runs the Java program using the bundled JAR file
5. Copies the generated KPOINTS file to the target directory

## License

[APACHE License](LICENSE-APACHE)

## Acknowledgments

This package is a wrapper around the k-point grid generator developed by the Mueller Group at Johns Hopkins University.

- [GitLab original repo](https://gitlab.com/muellergroup/k-pointGridGenerator)
- [Group website](https://muellergroup.jhu.edu/K-Points.html)
