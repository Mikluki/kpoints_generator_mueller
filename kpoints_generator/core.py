import os
import subprocess
from pathlib import Path
from typing import Optional

import pkg_resources

from .logs import LOGGER


class KPointsGenerationError(Exception):
    """Exception raised when k-points generation fails."""

    pass


def get_resource_path(resource_name):
    """Get the path to a resource file bundled with the package."""
    return pkg_resources.resource_filename(
        "kpoints_generator", f"java_resources/{resource_name}"
    )


# Store paths to resources globally to avoid repeated lookups
_JAR_PATH: Optional[str] = None
_COLLECTIONS_PATH: Optional[str] = None


def _init_resource_paths():
    """Initialize global resource paths if not already done."""
    global _JAR_PATH, _COLLECTIONS_PATH
    if _JAR_PATH is None:
        _JAR_PATH = get_resource_path("GridGenerator.jar")
        # Get directory containing the JAR file
        jar_dir = Path(_JAR_PATH).parent
        # Set collections path to the directory CONTAINING minDistanceCollections (not the directory itself)
        _COLLECTIONS_PATH = str(jar_dir)


def generate_kpoints(
    mindistance,
    vasp_directory=None,
    precalc_params=None,
    output_file="KPOINTS",
    save_precalc=True,
):
    """
    Generate a KPOINTS file using the Java-based GridGenerator.

    Parameters:
    -----------
    mindistance : float
        The minimum distance parameter for k-point grid generation.
    vasp_directory : str, optional
        Directory containing VASP input files. Defaults to current directory.
    precalc_params : dict, optional
        Additional parameters for the PRECALC file.
    output_file : str, optional
        Name of the output file. Defaults to 'KPOINTS'.
    save_precalc : bool, optional
        Whether to save the PRECALC file in the vasp_directory. Defaults to True.

    Returns:
    --------
    str
        Path to the generated KPOINTS file.

    Raises:
    -------
    KPointsGenerationError
        If the k-points generation fails.
    """
    # Initialize global resource paths if needed
    _init_resource_paths()

    # Make sure global paths are initialized
    if _JAR_PATH is None or _COLLECTIONS_PATH is None:
        raise KPointsGenerationError("Failed to initialize resource paths")

    # Use current directory if no VASP directory is specified
    if vasp_directory is None:
        vasp_directory = Path.cwd()
    else:
        vasp_directory = Path(vasp_directory)

    # Check for required input file (POSCAR) - fast fail if missing
    poscar_path = vasp_directory / "POSCAR"
    if not poscar_path.exists():
        raise KPointsGenerationError(
            "POSCAR file not found in the specified directory."
        )

    # Create PRECALC content
    precalc_content = f"MINDISTANCE={mindistance}\n"
    if precalc_params:
        for key, value in precalc_params.items():
            precalc_content += f"{key}={value}\n"

    # Create PRECALC file in the vasp_directory
    precalc_path = vasp_directory / "PRECALC"
    try:
        with open(precalc_path, "w") as f:
            f.write(precalc_content)

        # Construct Java command - reuse the same command structure for all calls
        java_cmd = [
            "java",
            f"-DLATTICE_COLLECTIONS={_COLLECTIONS_PATH}",
            "-Xms512m",
            "-Xmx2048m",
            "-jar",
            _JAR_PATH,
            str(vasp_directory),  # Use absolute path instead of "./"
        ]

        # Log the exact command for debugging
        LOGGER.debug(f"Running command: {' '.join(java_cmd)}")

        # Run Java with real-time output display
        subprocess.run(
            java_cmd,
            check=True,
            # No stdout/stderr capture so the output appears in real-time
        )
        LOGGER.info("--- k-points generation completed ---\n")

        # Check if KPOINTS file was generated
        kpoints_path = vasp_directory / "KPOINTS"
        if kpoints_path.exists():
            # Rename if a different output filename was requested
            if output_file != "KPOINTS":
                destination = vasp_directory / output_file
                os.replace(
                    kpoints_path, destination
                )  # Using os.replace for atomic operation
                kpoints_path = destination

            # Clean up the PRECALC file if not requested to save
            if not save_precalc:
                os.unlink(precalc_path)

            return str(kpoints_path)
        else:
            raise KPointsGenerationError(
                "KPOINTS file was not generated. Check VASP directory for errors."
            )

    except subprocess.CalledProcessError as e:
        # Clean up PRECALC if not saving and an error occurred
        if not save_precalc and precalc_path.exists():
            try:
                os.unlink(precalc_path)
            except OSError:
                pass  # Ignore cleanup errors

        raise KPointsGenerationError(f"Error running Java GridGenerator: {e}")
    except Exception as e:
        # Clean up PRECALC if not saving and an error occurred
        if not save_precalc and precalc_path.exists():
            try:
                os.unlink(precalc_path)
            except OSError:
                pass  # Ignore cleanup errors

        raise KPointsGenerationError(f"Unexpected error: {e}")


# This function can be called once at module import time
def check_prerequisites():
    """Check if all prerequisites for the k-points generation are met."""
    prerequisites_met = True
    issues = []

    # Check Java installation and version
    try:
        java_process = subprocess.run(
            ["java", "-version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Java version is typically output to stderr
        java_output = java_process.stderr
        LOGGER.info(f"Found Java: {java_output.splitlines()[0]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        prerequisites_met = False
        issues.append("Java is not installed or not in the PATH.")

    # Initialize and check resource paths
    _init_resource_paths()

    # Check if the resource paths were initialized properly
    if _JAR_PATH is None:
        prerequisites_met = False
        issues.append("Failed to initialize path to GridGenerator.jar")
    # Check if the JAR file is available
    elif not Path(_JAR_PATH).exists():
        prerequisites_met = False
        issues.append(f"GridGenerator.jar not found at {_JAR_PATH}")
    else:
        LOGGER.info(f"Found GridGenerator.jar at: {_JAR_PATH}")

    # Check if the collections path was initialized properly
    if _COLLECTIONS_PATH is None:
        prerequisites_met = False
        issues.append("Failed to initialize path to minDistanceCollections")
    # Check if the database directory is available
    elif not Path(_COLLECTIONS_PATH).exists():
        prerequisites_met = False
        issues.append(
            f"minDistanceCollections directory not found at {_COLLECTIONS_PATH}"
        )
    else:
        LOGGER.info(f"Found minDistanceCollections at: {_COLLECTIONS_PATH}")

    if prerequisites_met:
        return True, "All prerequisites met."
    else:
        return False, "Missing prerequisites: " + "; ".join(issues)
