"""
kpoints_generator - A Python wrapper for the k-point grid generator Java package.

This package provides a simple way to generate k-point grids for VASP calculations
using the GridGenerator Java package.
"""

from .core import KPointsGenerationError, check_prerequisites, generate_kpoints

__version__ = "0.1.0"
__all__ = ["generate_kpoints", "check_prerequisites", "KPointsGenerationError"]
