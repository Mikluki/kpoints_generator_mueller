import kpoints_generator as kpg

# # Check if all prerequisites are met
# success, message = kpg.check_prerequisites()
# if not success:
#     print(f"Warning: {message}")

# Generate a KPOINTS file in the current directory
kpoints_file = kpg.generate_kpoints(
    mindistance=55,  # Required parameter
    vasp_directory="example_05",  # Optional, defaults to current dir
    precalc_params={  # Optional additional parameters for PRECALC
        "INCLUDEGAMMA": "AUTO",
    },
    output_file="KPOINTS",  # Optional, defaults to "KPOINTS"
)
