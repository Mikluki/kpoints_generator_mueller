import shutil
import subprocess
import tempfile
from pathlib import Path

import pkg_resources


class KPointsGenerationError(Exception):
    """Exception raised when k-points generation fails."""

    pass


def get_resource_path(resource_name):
    """Get the path to a resource file bundled with the package."""
    return pkg_resources.resource_filename(
        "kpoints_generator", f"java_resources/{resource_name}"
    )


def generate_kpoints(
    mindistance, vasp_directory=None, precalc_params=None, output_file="KPOINTS"
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

    Returns:
    --------
    str
        Path to the generated KPOINTS file.

    Raises:
    -------
    KPointsGenerationError
        If the k-points generation fails.
    """
    # Use current directory if no VASP directory is specified
    if vasp_directory is None:
        vasp_directory = Path.cwd()
    vasp_directory = Path(vasp_directory)

    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy necessary VASP files to the temp directory
        for file in ["POSCAR", "INCAR"]:
            fpath = Path(vasp_directory, file)
            if fpath.exists():
                shutil.copy(fpath, temp_dir)

        # Create PRECALC file
        precalc_path = Path(temp_dir, "PRECALC")
        with open(precalc_path, "w") as f:
            f.write(f"MINDISTANCE={mindistance}\n")
            if precalc_params:
                for key, value in precalc_params.items():
                    f.write(f"{key}={value}\n")

        # Get paths to Java resources
        jar_path = get_resource_path("GridGenerator.jar")

        # Make sure the minDistanceCollections directory is in the same path as the JAR
        # db_path = get_resource_path("minDistanceCollections")

        # Create custom getKPoints script with correct paths
        script_content = _create_get_kpoints_script(jar_path=Path(jar_path).parent)

        script_path = Path(temp_dir, "getKPoints")
        with open(script_path, "w") as f:
            f.write(script_content)

        # Make the script executable
        script_path.chmod(0o755)

        # Run the script
        try:
            result = subprocess.run(
                [script_path],
                cwd=temp_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Copy the generated KPOINTS file to the target directory
            kpoints_path = Path(temp_dir) / "KPOINTS"
            if kpoints_path.exists():
                destination = Path(vasp_directory) / output_file
                shutil.copy(kpoints_path, destination)
                return destination
            else:
                raise KPointsGenerationError(
                    f"KPOINTS file was not generated. Output: {result.stdout}\nError: {result.stderr}"
                )
        except subprocess.CalledProcessError as e:
            raise KPointsGenerationError(
                f"Error running getKPoints: {e.stdout}\n{e.stderr}"
            )


def _create_get_kpoints_script(jar_path):
    """Create the getKPoints script with the correct paths."""
    script = f"""#!/bin/bash
# User's local variables

# The folder containing the GridGenerator.jar. 
# Please give the absolute path.
JAR_PATH="{jar_path}"

# switch to control whether to call the server when the local
# version is not found. (No longer supported, always FALSE)
CALL_SERVER_IF_LOCAL_MISSING="FALSE"

# The script assumes the minDistanceCollections is in the same 
# folder as GridGenerator. If not, users can set it themselves.
LATTICE_COLLECTIONS="$JAR_PATH"

################################################################
# Generally, user doesn't need touch everything below here.

version="Python-wrapped C2020.11.25" 
echo "Running getKPoints script version" $version".";

# This switch controls the information regarding grid generation output file.
# The default is "TRUE", replacing it with "FALSE" or any other values will turn it off.
list_message="TRUE"

# These format the messages accordingly
warning_message()
{{
  echo "*** WARNING: $1 ***"
}}

error_message()
{{
  echo "*** ERROR: $1 ***"
}}

# Check for early kill signals.
killed()
{{
  error_message "Command was terminated by user."
}}
trap 'killed' 1 2 3

failed_to_connect()
{{
  error_message "There is a problem connecting to the database."
}}
trap 'failed_to_connect' 6 7 10 27

# Generate grid for VASP using local JAR file
generate_grid_for_vasp_jar() 
{{
    if ! java -version > /dev/null 2>&1 ; then
        error_message "Local installation of JAVA is not found."
        return 1
    fi

    if [ -z ${{JAR_PATH}} ] || [ ! -e ${{JAR_PATH}}/GridGenerator.jar ]; then
        error_message "Local installation of k-pointGridGenerator is not found."
        return 1
    fi

    echo "Generating grid using local installation at ${{JAR_PATH}} ..."
    if [ ! -f INCAR ]; then
        warning_message "No INCAR file detected. Using only symmetry information from structure file."
    fi

    java -DLATTICE_COLLECTIONS="${{LATTICE_COLLECTIONS}}" -Xms512m -Xmx2048m -jar ${{JAR_PATH}}/GridGenerator.jar ./
    return 0
}}

# Check variables and decide whether to use local JAR 
generate_grid_for_vasp(){{
    generate_grid_for_vasp_jar
    if [ $? -ne 0 ]; then
        error_message "Failed to generate k-points grid."
        exit 1
    fi
}}

# Check if PRECALC file exists
precalc_default="FALSE"
check_precalc()
{{
  if [ -f PRECALC ]; then 
    precalc_default="FALSE"
  else # In the case PRECALC does not exists, create an empty file to feed in
    warning_message "No PRECALC file detected. Using default values."
    touch PRECALC
    precalc_default="TRUE"
  fi   
}}

# Write output to stdout
output_to_stdout() {{
  if [ -e KPOINTS ]; then
    echo "=============== CONTENT OF KPOINTS ==============="
    cat KPOINTS
  fi
}}

################################# main() ######################################
check_precalc

# Check if POSCAR exists
if [ ! -f POSCAR ]; then
    error_message "POSCAR file not found! Exit."
    exit 1
fi

# Generate the grid
generate_grid_for_vasp

# Final cleanup
if [ "$precalc_default" == "TRUE" ]; then
  rm PRECALC
fi

# Output KPOINTS content if requested
if [ "$precalc_default" == "FALSE" ] && [ -e PRECALC ]; then
  write_vectors=$( grep -iE "^[ ]*WRITE_LATTICE_VECTORS" ./PRECALC 2> /dev/null | \\
    awk -F "[=#]" '{{ print tolower($2) }}' | tr -d [:space:] 2> /dev/null )
  if [ ! -z $write_vectors ] && [ $write_vectors == "true" ]; then
    output_to_stdout
  fi
fi

echo "Finished."
"""
    return script


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
        print(f"Found Java: {java_output.splitlines()[0]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        prerequisites_met = False
        issues.append("Java is not installed or not in the PATH.")

    # Check if the JAR file is available
    jar_path = get_resource_path("GridGenerator.jar")
    if not Path(jar_path).exists():
        prerequisites_met = False
        issues.append(f"GridGenerator.jar not found at {jar_path}")
    else:
        print(f"Found GridGenerator.jar at: {jar_path}")

    # Check if the database directory is available
    db_path = get_resource_path("minDistanceCollections")
    if not Path(db_path).exists():
        prerequisites_met = False
        issues.append(f"minDistanceCollections directory not found at {db_path}")
    else:
        print(f"Found minDistanceCollections at: {db_path}")

    if prerequisites_met:
        return True, "All prerequisites met."
    else:
        return False, "Missing prerequisites: " + "; ".join(issues)
