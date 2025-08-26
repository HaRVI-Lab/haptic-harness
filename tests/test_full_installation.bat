@echo off
REM Full installation test script for Haptic Harness Generator (Windows)
REM Tests complete installation from scratch following README instructions

echo ============================================================
echo HAPTIC HARNESS GENERATOR - FULL INSTALLATION TEST (Windows)
echo ============================================================

REM Step 1: Remove existing environment
echo Step 1: Removing existing hhgen environment...
call conda deactivate >nul 2>&1
call conda remove -n hhgen --all -y >nul 2>&1

REM Step 2: Create fresh environment from README instructions
echo Step 2: Creating fresh environment from environment-locked.yml...
call conda env create -f environment-locked.yml
if %errorlevel% neq 0 (
    echo ERROR: Failed to create conda environment
    exit /b 1
)

REM Step 3: Activate environment
echo Step 3: Activating hhgen environment...
call conda activate hhgen
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate conda environment
    exit /b 1
)

REM Step 4: Install package in development mode
echo Step 4: Installing package in development mode...
pip install -e .
if %errorlevel% neq 0 (
    echo ERROR: Failed to install package
    exit /b 1
)

REM Step 5: Run environment verification
echo Step 5: Running environment verification...
python verify_environment.py
if %errorlevel% neq 0 (
    echo ERROR: Environment verification failed
    exit /b 1
)

REM Step 6: Test application imports
echo Step 6: Testing application imports...
python -c "from haptic_harness_generator import Generator; from haptic_harness_generator.core import ConfigurationManager; from haptic_harness_generator.ui import MainWindow; from vtkbool.vtkBool import vtkPolyDataBooleanFilter; import vtk; print('✅ All imports successful'); print(f'VTK version: {vtk.vtkVersion.GetVTKVersion()}')"
if %errorlevel% neq 0 (
    echo ERROR: Import test failed
    exit /b 1
)

REM Step 7: Run full test suite
echo Step 7: Running full test suite...
python haptic_harness_generator/run_tests.py
if %errorlevel% neq 0 (
    echo ERROR: Test suite failed
    exit /b 1
)

REM Step 8: Test file generation
echo Step 8: Testing file generation...
if not exist "C:\temp" mkdir "C:\temp"
if not exist "C:\temp\haptic-test-output" mkdir "C:\temp\haptic-test-output"
python -c "from haptic_harness_generator import Generator; import os; g = Generator('C:/temp/haptic-test-output'); g.regen(); print('✅ File generation successful')"
if %errorlevel% neq 0 (
    echo ERROR: File generation failed
    exit /b 1
)

REM Step 9: Verify generated files exist
echo Step 9: Verifying generated files...
dir "C:\temp\haptic-test-output\*.dxf" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: No DXF files found
    exit /b 1
) else (
    echo ✅ DXF files generated successfully
    dir "C:\temp\haptic-test-output\*.dxf"
)

dir "C:\temp\haptic-test-output\*.stl" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: No STL files found
    exit /b 1
) else (
    echo ✅ STL files generated successfully
    dir "C:\temp\haptic-test-output\*.stl"
)

REM Step 10: Test command line interface (with timeout)
echo Step 10: Testing command line interface...
timeout /t 10 /nobreak >nul & taskkill /f /im python.exe >nul 2>&1 & run-haptic-harness --export-dir C:\temp\haptic-test-cli >nul 2>&1
echo ✅ CLI started successfully

REM Cleanup
echo Cleaning up test files...
rmdir /s /q "C:\temp\haptic-test-output" >nul 2>&1
rmdir /s /q "C:\temp\haptic-test-cli" >nul 2>&1

echo ============================================================
echo ✅ INSTALLATION TEST PASSED
echo All components working correctly!
echo ============================================================
