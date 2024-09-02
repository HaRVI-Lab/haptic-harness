# Haptic Harness Toolkit Generator

A software to easily generate parameterized tiles for haptic harnesses

## Description

-   This software allows researchers to create an easy haptic harness by generating a tile solution
-   Researchers can change harness parameters to meet their needs

## Getting Started

Setting up a new Conda environment through the ternminal with the correct dependencies:

1. Create a new conda environment with Python 3.9 using: `conda create -n hapticsHarnessGenerator python=3.9`
2. Install VTKBool with: `conda install -c conda-forge vtkbool` (ensure conda-forge is in your conda config)
3. Install ezdxf with: `pip install haptic_harness_generator`

## Software Operation

1. Change parameters in the "Generate Tiles" tab
2. In the "Generaet Tiles" tab, click "Generate Parts" to generate the .dxf files
3. In the "Generate Peripherals" tab, Click "Generate Parts" to generate the .stl files
4. Generated files can be found in the "exports" directory
![Alt text](anatomyOfTile.png)
## Dependencies:

-   Pyvista
-   vtkbool
-   ezdxf
-   Numpy
-   PyQT5
-   pyvistaqt
