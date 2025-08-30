# Haptic Harness Toolkit Generator
A software to easily generate parameterized tiles for haptic harnesses
<p align="center">
 <img src = "haptic_harness_generator/assets/hexagonExploded.jpg" alt = "Exploded view of hexagonal tile" width="30%">
 <img src = "haptic_harness_generator/assets/flatView.jpg" alt = "Flat view of tile" width="30%">
 <img src = "haptic_harness_generator/assets/squareExploded.jpg" alt = "Exploded view of square tile" width="30%">
</p>

## Description
-   This software allows researchers to create an easy haptic harness by generating a tile solution
-   Researchers can change harness parameters to meet their needs

## Installation

### Requirements
- Anaconda or Miniconda
- Git

### Steps
1. Clone repository:
   ```bash
   git clone https://github.com/HaRVI-Lab/haptic-harness.git
   cd haptic-harness
   ```

2. Create conda environment (Windows and Linux users):
   ```bash
   conda env create -f environment-locked.yml
   conda activate hhgen
   ```
   For Mac users with M-series chips:
   ```bash
   CONDA_SUBDIR=osx-64 conda env create -f environment-locked.yml
   conda activate hhgen
   ```


3. Install package in development mode:
   ```bash
   pip install -e .
   ```

4. Verify installation:
   ```bash
   python verify_environment.py
   ```

5. Run application:
   ```bash
   run-haptic-harness --export-dir /absolute/path/to/exports
   ```

## Troubleshooting

If installation fails:
1. Remove the environment: `conda remove -n hhgen --all`
2. Update conda: `conda update conda`
3. Retry installation from Step 2

## Software Operation
1. Change parameters in the "Generate Tiles" tab
2. In the "Generate Tiles" tab, click "Generate Parts" to generate the .dxf and .stl files
3. Generated files can be found in the "exports" directory
<p align= "center">
    <img src = "haptic_harness_generator/assets/hapticsNew.jpg" alt = "Diagram view" width="76%">
</p>

## Hardware Operation
### Materials
- Tyvek: will be cut for the tiles
- EVA foam: will be cut for the liner
- Hardboard (or comparable material): will be cut for the magnet ring
- Hard 3D printable material (ex. PLA): will be print for peripheral items

### Tile Assembly
-   After files are generated, they will be exported as:
    -   .dxf files to be cut on a laser cutter (.dxf files can be converted online or in software like Adobe Illustrator)
    -   .stl files to be 3D-printed
-   A tile is constructed by supergluing the cut parts as shown below: 
<p align="center">
    <img src = "haptic_harness_generator/assets/diagramOne.jpg" alt = "Diagram view" width="50%">
</p>

## Dependencies:
-   Pyvista
-   vtkbool=3.0.1 (pinned version for compatibility)
-   vtk=9.3.0 (pinned version for compatibility)
-   ezdxf
-   Numpy
-   PyQT5
-   pyvistaqt

# Citations for Haptic Harness Generator
## APA Format
Kollannur, S. Z. G., Robertson, K., & Culbertson, H. (2025). *Haptic Harness Generator* [Computer software]. GitHub. https://github.com/HaRVI-Lab/haptic-harness
## MLA Format
Kollannur, Sandeep, Katie Robertson, and Heather Culbertson. *Haptic Harness Generator*. Computer software. GitHub, 2025. Web. https://github.com/HaRVI-Lab/haptic-harness.
## Chicago Format
Kollannur, Sandeep, Katie Robertson, and Heather Culbertson. Haptic Harness Generator. Computer software. 2025. https://github.com/HaRVI-Lab/haptic-harness.
## BibTeX Format
```bibtex
@software{kollannur2025haptic,
  author = {Kollannur, Sandeep and Robertson, Katie and Culbertson, Heather},
  title = {Haptic Harness Generator},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  url = {https://github.com/HaRVI-Lab/haptic-harness}
}
```
## Software Citation Format
Sandeep Kollannur, Katie Robertson, and Heather Culbertson. (2025). Haptic Harness Generator: A software to easily generate parameterized tiles for haptic harnesses. GitHub. https://github.com/HaRVI-Lab/haptic-harness
