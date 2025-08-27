# Segmentation Fault Troubleshooting Guide

## Problem Description
The haptic harness generator works fine on your main computer but crashes with "Segmentation fault (core dumped)" on a mini PC with the same Linux Mint x86 environment, right after displaying "The software may take a minute before startup..."

## Root Cause Analysis
This is almost certainly a **VTK/OpenGL/Graphics initialization issue**. The segfault occurs when:
1. PyVistaQt tries to initialize OpenGL contexts
2. VTK attempts to create rendering windows
3. Qt tries to set up graphics acceleration
4. The mini PC lacks proper graphics drivers or OpenGL support

## Immediate Solutions

### 1. Run Diagnostics First
```bash
python diagnose_segfault.py
```
This will test each component incrementally to identify exactly where the crash occurs.

### 2. Try Headless Mode
```bash
python run_headless.py --export-dir /tmp/haptic_test
```
This bypasses all GUI components and generates files directly.

### 3. Apply Segfault Fix
```bash
python fix_segfault.py
```
This patches the main application with better error handling and automatic fallback to headless mode.

### 4. Test with Fixed Version
```bash
run-haptic-harness --export-dir /tmp/haptic_test --headless
```

## Detailed Troubleshooting Steps

### Step 1: System Requirements Check
```bash
# Check OpenGL support
glxinfo -B

# Check graphics drivers
lspci | grep -i vga
lsmod | grep -i nvidia
lsmod | grep -i radeon

# Check display
echo $DISPLAY
xdpyinfo | head -10
```

### Step 2: Environment Variables Fix
Add these to your shell profile (`~/.bashrc` or `~/.zshrc`):
```bash
# For headless operation
export QT_QPA_PLATFORM=offscreen
export VTK_SILENCE_GET_VOID_POINTER_WARNINGS=1
export DISPLAY=:99

# For software rendering (if hardware acceleration fails)
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
```

### Step 3: Conda Environment Fixes
```bash
# Recreate environment with specific graphics packages
conda remove -n hhgen --all
conda env create -f environment-locked.yml
conda activate hhgen

# Install additional graphics support
conda install -c conda-forge mesa-libgl-devel-cos6-x86_64
conda install -c conda-forge libgl1-mesa-glx

pip install -e .
```

### Step 4: Alternative VTK Backend
If the issue persists, try forcing software rendering:
```bash
# Before running the application
export VTK_USE_OFFSCREEN=1
export VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN=1
```

## Hardware-Specific Solutions

### For Intel Graphics (Common on Mini PCs)
```bash
# Install Intel graphics drivers
sudo apt update
sudo apt install intel-media-va-driver-non-free
sudo apt install mesa-utils

# Test OpenGL
glxgears
```

### For Headless/Server Systems
```bash
# Install virtual display
sudo apt install xvfb

# Run with virtual display
xvfb-run -a python run_headless.py --export-dir /tmp/test
```

### For Systems with Limited Graphics Memory
```bash
# Reduce graphics requirements
export VTK_VOLUME_RENDERING_MODE=0
export PYVISTA_OFF_SCREEN=true
```

## Code-Level Fixes Applied

The `fix_segfault.py` script applies these changes:

1. **Safe Graphics Initialization**: Detects headless environments and configures Qt accordingly
2. **Graceful Fallback**: If GUI fails, automatically switches to headless mode
3. **Better Error Handling**: Catches segfaults and provides helpful error messages
4. **Environment Detection**: Automatically configures for different system types

## Testing Your Fix

### Test 1: Basic Functionality
```bash
python diagnose_segfault.py
```
Should complete all tests without crashing.

### Test 2: Headless Generation
```bash
python run_headless.py --export-dir /tmp/test --preset "Standard 4-sided"
```
Should generate STL and DXF files.

### Test 3: GUI with Fallback
```bash
run-haptic-harness --export-dir /tmp/test
```
Should either show GUI or fallback to headless mode gracefully.

## Prevention for Future Deployments

### 1. Pre-deployment Check Script
```bash
#!/bin/bash
# Check graphics capabilities before installation
glxinfo -B > /dev/null 2>&1 || echo "WARNING: No OpenGL support detected"
python -c "import vtk; print('VTK OK')" || echo "ERROR: VTK not working"
```

### 2. Docker/Container Solution
Consider containerizing the application with proper graphics support:
```dockerfile
FROM continuumio/miniconda3
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libxext6 \
    libsm6 \
    libice6
```

### 3. System Requirements Documentation
Update installation docs to include:
- Minimum OpenGL version requirements
- Graphics driver recommendations
- Headless mode instructions for servers

## If All Else Fails

### Last Resort Options:
1. **Use Windows version** on the mini PC (you mentioned it works on Windows)
2. **Remote desktop** from mini PC to main computer
3. **Network generation**: Run generator on main computer, access via network
4. **Container solution**: Use Docker with proper graphics forwarding

## Reporting Issues

If none of these solutions work, collect this information:
```bash
# System info
uname -a
lscpu
lspci | grep -i vga
glxinfo -B

# Python environment
python --version
conda list | grep -E "(vtk|pyvista|qt)"

# Error details
python diagnose_segfault.py > diagnostic_output.txt 2>&1
```

The segfault is definitely solvable - it's a common issue with VTK applications on systems with limited graphics support!
