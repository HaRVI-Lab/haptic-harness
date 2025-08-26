#!/bin/bash
# Full installation test script for Haptic Harness Generator
# Tests complete installation from scratch following README instructions

set -e  # Exit on any error

echo "============================================================"
echo "HAPTIC HARNESS GENERATOR - FULL INSTALLATION TEST"
echo "============================================================"

# Step 1: Remove existing environment
echo "Step 1: Removing existing hhgen environment..."
conda deactivate 2>/dev/null || true
conda remove -n hhgen --all -y 2>/dev/null || true

# Step 2: Create fresh environment from README instructions
echo "Step 2: Creating fresh environment from environment-locked.yml..."
conda env create -f environment-locked.yml

# Step 3: Activate environment
echo "Step 3: Activating hhgen environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate hhgen

# Step 4: Install package in development mode
echo "Step 4: Installing package in development mode..."
pip install -e .

# Step 5: Run environment verification
echo "Step 5: Running environment verification..."
python verify_environment.py

# Step 6: Test application imports
echo "Step 6: Testing application imports..."
python -c "
from haptic_harness_generator import Generator
from haptic_harness_generator.core import ConfigurationManager
from haptic_harness_generator.ui import MainWindow
from vtkbool.vtkBool import vtkPolyDataBooleanFilter
import vtk
print('✅ All imports successful')
print(f'VTK version: {vtk.vtkVersion.GetVTKVersion()}')
"

# Step 7: Run full test suite
echo "Step 7: Running full test suite..."
python haptic_harness_generator/run_tests.py

# Step 8: Test file generation
echo "Step 8: Testing file generation..."
mkdir -p /tmp/haptic-test-output
python -c "
from haptic_harness_generator import Generator
import os
g = Generator('/tmp/haptic-test-output')
g.regen()
print('✅ File generation successful')
"

# Step 9: Verify generated files exist
echo "Step 9: Verifying generated files..."
if ls /tmp/haptic-test-output/*.dxf 1> /dev/null 2>&1; then
    echo "✅ DXF files generated successfully"
    ls -la /tmp/haptic-test-output/*.dxf
else
    echo "❌ No DXF files found"
    exit 1
fi

if ls /tmp/haptic-test-output/*.stl 1> /dev/null 2>&1; then
    echo "✅ STL files generated successfully"
    ls -la /tmp/haptic-test-output/*.stl
else
    echo "❌ No STL files found"
    exit 1
fi

# Step 10: Test command line interface
echo "Step 10: Testing command line interface..."
timeout 10s run-haptic-harness --export-dir /tmp/haptic-test-cli || {
    if [ $? -eq 124 ]; then
        echo "✅ CLI started successfully (timed out as expected)"
    else
        echo "❌ CLI failed to start"
        exit 1
    fi
}

# Cleanup
echo "Cleaning up test files..."
rm -rf /tmp/haptic-test-output
rm -rf /tmp/haptic-test-cli

echo "============================================================"
echo "✅ INSTALLATION TEST PASSED"
echo "All components working correctly!"
echo "============================================================"
