# Haptic Harness Toolkit Generator
A software to easily generate parameterized tiles for haptic harnesses
<p align="center">
 <img src = "images/hexagonExploded.jpg" alt = "Exploded view of hexagonal tile" width="30%">
 <img src = "images/flatView.jpg" alt = "Flat view of tile" width="30%">
 <img src = "images/squareExploded.jpg" alt = "Exploded view of square tile" width="30%">
</p>

## Description
-   This software allows researchers to create an easy haptic harness by generating a tile solution
-   Researchers can change harness parameters to meet their needs

## Getting Started
Setting up a new Conda environment through the terminal with the correct dependencies:

**IMPORTANT**: Due to package compatibility issues between different installation sources, follow these platform-specific instructions carefully:

### For Windows (64-bit)
1. Create environment: `conda create -n hh-gen python=3.9 vtk -c conda-forge --platform win-64`
2. Activate environment: `conda activate hh-gen`
3. **Install vtkbool via pip**: `pip install vtkbool`
4. Install the haptic harness generator: `pip install haptic_harness_generator`

### For Linux (64-bit)
1. Create environment: `conda create -n hh-gen python=3.9 vtk -c conda-forge --platform linux-64`
2. Activate environment: `conda activate hh-gen`
3. **Install vtkbool via pip**: `pip install vtkbool`
4. Install the haptic harness generator: `pip install haptic_harness_generator`

### For Intel Mac (64-bit)
1. Create environment: `conda create -n hh-gen python=3.9 vtk -c conda-forge --platform osx-64`
2. Activate environment: `conda activate hh-gen`
3. **Install vtkbool via pip**: `pip install vtkbool`
4. Install the haptic harness generator: `pip install haptic_harness_generator`

### For Apple Silicon Mac (M1/M2/M3)
1. Create environment: `conda create -n hh-gen python=3.9 vtk -c conda-forge --platform osx-arm64`
2. Activate environment: `conda activate hh-gen`
3. **Install vtkbool via pip**: `pip install vtkbool`
4. Install the haptic harness generator: `pip install haptic_harness_generator`

> [!WARNING]  
> **Critical Installation Note**: Do NOT install `vtkbool` through conda-forge as it has incompatible import paths with this application. Always use `pip install vtkbool` after creating the conda environment with vtk. The conda-forge version uses `vtkbool.vtkbool` imports while this application expects `vtkbool.vtkBool` imports.

> [!TIP]
> If you're unsure of your platform, you can omit the `--platform` flag and conda will auto-detect, but you must still install vtkbool via pip.

### Running the Application
5. Run the program from your command line with: 
   -   `run-haptic-harness --export-dir [your absolute path]`
   -   **Windows example**: `run-haptic-harness --export-dir C:\Users\Me\Downloads`
   -   **Linux/Mac example**: `run-haptic-harness --export-dir ~/Downloads/hh-v1`

## Software Operation
1. Change parameters in the "Generate Tiles" tab
2. In the "Generate Tiles" tab, click "Generate Parts" to generate the .dxf and .stl files
3. Generated files can be found in the "exports" directory
<p align= "center">
    <img src = "images/hapticsNew.jpg" alt = "Diagram view" width="76%">
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
    <img src = "images/diagramOne.jpg" alt = "Diagram view" width="50%">
</p>

## Dependencies:
-   Pyvista
-   vtkbool (installed via pip, not conda)
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
