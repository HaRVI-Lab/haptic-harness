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

Setting up a new Conda environment through the ternminal with the correct dependencies:

1. Create a new conda environment with Python 3.9 using: `conda create -n hapticHarnessGenerator python=3.9 vtkbool vtk -c conda-forge`
> [!WARNING]  
> vtkbool through conda-forge is only availabe on win64, linux64, and osx64. Please see: https://github.com/zippy84/vtkbool  
> Therefore, please select the correct platform for the conda environment like this example for mac: `conda create -n hapticHarnessGenerator python=3.9 vtkbool vtk -c conda-forge --platform osx-64`
> You could also run `conda create -n hapticHarnessGenerator python=3.9 vtkbool vtk -c conda-forge` for other os, like linux or `conda create -n hapticHarnessGenerator python=3.9 vtkbool vtk -c conda-forge --platform osx-arm64` for Apple silicon.
2. Run: `conda activate hapticHarnessGenerator`
3. Install the haptic harness generator with: `pip install haptic_harness_generator`
4. Run the program from your cli with: 
   -   `run-haptic-harness --export-dir [your absolute path]`
   -   Ex. (for Windows) `run-haptic-harness --export-dir C:\Users\Me\Downloads` 


## Software Operation

1. Change parameters in the "Generate Tiles" tab
2. In the "Generaet Tiles" tab, click "Generate Parts" to generate the .dxf and .stl files
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
    -   .dxf files to be cut on a laser cutter (.dxf files can be converetd online or in software like Adobe Illustrator)
    -   .stl files to be 3D-printed
-   A tile is constructed by supergluing the cut parts as shown below: 
<p align="center">
    <img src = "images/diagramOne.jpg" alt = "Diagram view" width="50%">
</p>

## Dependencies:

-   Pyvista
-   vtkbool
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

