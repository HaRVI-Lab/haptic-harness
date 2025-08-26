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

**IMPORTANT**: Use this tested cross-platform approach for reliable installation on any system:

### Step 1: Remove any existing environment (if you've tried before)
```bash
conda deactivate
conda remove -n hhgenerator --all -y
```

### Step 2: Create environment from specification (Cross-Platform Method)
Create a file called `haptic-env.yml` with this content:

```yaml
name: hhgenerator
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.9
  - vtk
  - vtkbool
```

Then create the environment:
```bash
conda env create -f haptic-env.yml
```

### Step 3: Activate environment
```bash
conda activate hhgenerator
```

### Step 4: Test vtkbool installation and create compatibility fix if needed

First, test if vtkbool works with the expected import:
```bash
python -c "from vtkbool.vtkBool import vtkPolyDataBooleanFilter; print('vtkbool working')"
```

**If you get an import error**, create the compatibility fix:
```bash
python -c "
import os
import vtkbool

# Find the vtkbool package location
vtkbool_path = vtkbool.__path__[0]
vtkbool_compat = os.path.join(vtkbool_path, 'vtkBool')

# Create compatibility directory and file
os.makedirs(vtkbool_compat, exist_ok=True)
with open(os.path.join(vtkbool_compat, '__init__.py'), 'w') as f:
    f.write('# Compatibility shim for vtkbool import paths\\n')
    f.write('from vtkbool.vtkbool import *\\n')
    
print('✓ Created vtkBool compatibility module')
"
```

Then test again:
```bash
python -c "from vtkbool.vtkBool import vtkPolyDataBooleanFilter; print('vtkbool working')"
```

### Step 5: Install the haptic harness generator
```bash
pip install haptic_harness_generator
```

> [!WARNING]  
> **Critical Installation Notes**: 
> - The conda-forge vtkbool package uses different import paths (`vtkbool.vtkbool`) than what this application expects (`vtkbool.vtkBool`)
> - The compatibility fix in Step 5 is **required** and must be run after installing vtkbool
> - If you get import errors, make sure you ran Step 5 correctly

> [!TIP]
> If you're unsure of your platform, you can omit the `--platform` flag and conda will auto-detect your system.

### Step 8: Run the application
```bash
run-haptic-harness --export-dir [your absolute path]
```

**Examples:**
- **Windows**: `run-haptic-harness --export-dir C:\Users\Me\Downloads`
- **Linux/Mac**: `run-haptic-harness --export-dir ~/Downloads/hh-v1`

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
-   vtkbool (installed via conda-forge with compatibility shim)
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
