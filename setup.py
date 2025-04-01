from setuptools import find_packages, setup

# Read the contents of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="kpoints_generator",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        "kpoints_generator": [
            "java_resources/GridGenerator.jar",
            "java_resources/getKPoints",
            "java_resources/minDistanceCollections/*",
        ],
    },
    include_package_data=True,
    # Metadata
    author="Mik Luki",
    author_email="None",
    description="A Python wrapper for the k-point grid generator Java package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="vasp, kpoints, dft, computational-chemistry",
    url="https://github.com/Mikluki/kpoints_generator_mueller",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    python_requires=">=3.6",
    # Dependencies
    install_requires=[
        # Add any Python dependencies here
    ],
    # Entry points for command-line usage
    entry_points={
        "console_scripts": [
            "kpoints-generator=kpoints_generator.cli:main",
        ],
    },
)
