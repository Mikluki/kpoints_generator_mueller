import argparse
import os
import sys

from .core import KPointsGenerationError, check_prerequisites, generate_kpoints


def main():
    """Command-line interface for kpoints_generator."""
    parser = argparse.ArgumentParser(
        description="Generate KPOINTS file for VASP calculations"
    )

    parser.add_argument(
        "--mindistance",
        "-m",
        type=float,
        required=True,
        help="Minimum distance parameter for k-point grid generation",
    )

    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default=os.getcwd(),
        help="Directory containing VASP input files (default: current directory)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="KPOINTS",
        help="Name of the output file (default: KPOINTS)",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if all prerequisites are met without generating k-points",
    )

    # Allow specifying PRECALC parameters directly from command line
    parser.add_argument(
        "--precalc-param",
        "-p",
        action="append",
        help="Additional PRECALC parameters in KEY=VALUE format",
    )

    args = parser.parse_args()

    # If --check is specified, only check prerequisites
    if args.check:
        success, message = check_prerequisites()
        print(message)
        sys.exit(0 if success else 1)

    # Parse additional PRECALC parameters from command line
    precalc_params = {}
    if args.precalc_param:
        for param in args.precalc_param:
            try:
                key, value = param.split("=", 1)
                precalc_params[key] = value
            except ValueError:
                print(
                    f"Warning: Ignoring invalid parameter format: {param}",
                    file=sys.stderr,
                )

    try:
        kpoints_file = generate_kpoints(
            mindistance=args.mindistance,
            vasp_directory=args.directory,
            precalc_params=precalc_params,
            output_file=args.output,
        )
        print(f"Successfully generated {kpoints_file}")
    except KPointsGenerationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
