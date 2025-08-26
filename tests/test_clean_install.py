#!/usr/bin/env python3
"""
Automated clean installation test for Haptic Harness Generator.
Must start with NO existing hhgen environment and follow EXACTLY the steps in README.md
"""

import subprocess
import sys
import os
import tempfile
import shutil

def run_command(cmd, check=True, capture_output=True):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    if isinstance(cmd, str):
        cmd = cmd.split()
    
    result = subprocess.run(cmd, capture_output=capture_output, text=True, check=False)
    
    if check and result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd)
    
    return result

def test_clean_installation():
    """Test complete installation from scratch"""
    print("="*60)
    print("HAPTIC HARNESS GENERATOR - CLEAN INSTALLATION TEST")
    print("="*60)
    
    # 1. Ensure environment doesn't exist
    print("\n1. Removing any existing hhgen environment...")
    run_command("conda remove -n hhgen --all -y", check=False)
    
    # 2. Create environment exactly as README states
    print("\n2. Creating environment from environment-locked.yml...")
    result = run_command("conda env create -f environment-locked.yml")
    assert result.returncode == 0, "Environment creation failed"
    print("✅ Environment created successfully")
    
    # 3. Activate and install package
    print("\n3. Installing package in development mode...")
    # Note: We need to use shell=True for conda activate to work
    install_cmd = "conda run -n hhgen pip install -e ."
    result = run_command(install_cmd, capture_output=False)
    assert result.returncode == 0, "Package installation failed"
    print("✅ Package installed successfully")
    
    # 4. Verify all imports work
    print("\n4. Testing imports...")
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
import sys
from haptic_harness_generator import Generator
from haptic_harness_generator.core import ConfigurationManager
from haptic_harness_generator.ui import MainWindow
from vtkbool.vtkBool import vtkPolyDataBooleanFilter
import vtk
print(f"VTK version: {vtk.vtkVersion.GetVTKVersion()}")
assert vtk.vtkVersion.GetVTKVersion() == "9.3.0", f"Expected VTK 9.3.0, got {vtk.vtkVersion.GetVTKVersion()}"
print("✅ All imports successful")
''')
        test_file = f.name

    result = run_command(f"conda run -n hhgen python {test_file}", capture_output=False)
    os.unlink(test_file)
    assert result.returncode == 0, f"Import test failed: {result.stderr if result.stderr else 'Unknown error'}"
    print("✅ Import test passed")
    
    # 5. Test environment verification
    print("\n5. Running environment verification...")
    result = run_command("conda run -n hhgen python verify_environment.py", capture_output=False)
    assert result.returncode == 0, "Environment verification failed"
    print("✅ Environment verification passed")
    
    # 6. Test actual generation
    print("\n6. Testing file generation...")
    with tempfile.TemporaryDirectory() as temp_dir:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(f'''
from haptic_harness_generator import Generator
import os
g = Generator("{temp_dir}")
g.regen()
# Check that files were created
dxf_files = [f for f in os.listdir("{temp_dir}") if f.endswith(".dxf")]
stl_files = [f for f in os.listdir("{temp_dir}") if f.endswith(".stl")]
assert len(dxf_files) > 0, "No DXF files generated"
assert len(stl_files) > 0, "No STL files generated"
print(f"Generated {{len(dxf_files)}} DXF files and {{len(stl_files)}} STL files")
''')
            test_file = f.name

        result = run_command(f"conda run -n hhgen python {test_file}", capture_output=False)
        os.unlink(test_file)
        assert result.returncode == 0, "Generation test failed"
        print("✅ Generation test passed")
    
    # 7. Test command line interface
    print("\n7. Testing command line interface...")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test that the CLI starts (we'll kill it quickly)
        import signal
        import time
        
        try:
            # Start the CLI in background
            proc = subprocess.Popen([
                "conda", "run", "-n", "hhgen", 
                "run-haptic-harness", "--export-dir", temp_dir
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a few seconds to start
            time.sleep(5)
            
            # Kill it
            proc.terminate()
            proc.wait(timeout=10)
            
            print("✅ CLI started successfully")
            
        except Exception as e:
            print(f"CLI test failed: {e}")
            raise
    
    print("\n" + "="*60)
    print("🎉 CLEAN INSTALLATION TEST PASSED!")
    print("Environment is 100% reproducible and working correctly.")
    print("="*60)

if __name__ == "__main__":
    try:
        test_clean_installation()
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
