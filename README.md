# Haptic Harness Toolkit Generator

A software to easily generate parameterized tiles for haptic harnesses
<div style = "display: flex; gap: 3%; justify-content: center;">
 <img src = "images/hexagonExploded.jpg" alt = "Exploded view of hexagonal tile" width="30%">
 <img src = "images/flatView.jpg" alt = "Flat view of tile" width="30%">
 <img src = "images/squareExploded.jpg" alt = "Exploded view of square tile" width="30%">
</div>

## Description

-   This software allows researchers to create an easy haptic harness by generating a tile solution
-   Researchers can change harness parameters to meet their needs

## Getting Started

Setting up a new Conda environment through the ternminal with the correct dependencies:

1. Create a new conda environment with Python 3.9 using: `conda create -n hapticHarnessGenerator python=3.9`
2. Run: `conda activate hapticHarnessGenerator`
3. Install VTKBool with: `conda install -c conda-forge vtkbool` (ensure conda-forge is in your conda config)
4. Install ezdxf with: `pip install haptic_harness_generator`
5. Run the program from your cli with: 
   -   `run-haptic-harness --export-dir [your absolute path]`
   -   Ex. (for Windows) `run-haptic-harness --export-dir C:\Users\Me\Downloads` 


## Software Operation

1. Change parameters in the "Generate Tiles" tab
2. In the "Generaet Tiles" tab, click "Generate Parts" to generate the .dxf files
3. In the "Generate Peripherals" tab, click "Generate Parts" to generate the .stl files
4. Generated files can be found in the "exports" directory
<div style = "display: flex; justify-content: center;">
    <img src = "images/anatomyOfTile.jpg" alt = "Diagram view" width="75%">
</div>

## Hardware Operation
### Materials
- Tyvek: will be cut for the tiles
- EVA foam: will be cut for the liner
- Hardboard (or comparable material): will be cut for the magnet ring
- Hard 3D printable material (ex. PLA): will be print for peripheral items
### Tile Assembly
-   After files are generated, they will be exported as:
    -   .dxf files to be cut on a laser cutter
    -   .stl files to be 3D-printed
-   A tile is constructed by supergluing the cut parts as shown below: 
<div style = "display: flex; justify-content: center;">
    <img src = "images/diagramOne.jpg" alt = "Diagram view" width="50%">
</div>

## Dependencies:

-   Pyvista
-   vtkbool
-   ezdxf
-   Numpy
-   PyQT5
-   pyvistaqt
