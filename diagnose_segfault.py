#!/usr/bin/env python3
"""
Diagnostic script to identify segmentation fault causes in haptic harness generator.
This script tests various components incrementally to isolate the problem.
"""

import sys
import os
import traceback

def test_basic_imports():
    """Test basic Python imports"""
    print("=== TESTING BASIC IMPORTS ===")
    try:
        import numpy as np
        print(f"✅ NumPy {np.__version__}")
    except Exception as e:
        print(f"❌ NumPy failed: {e}")
        return False
    
    try:
        import ezdxf
        print(f"✅ ezdxf {ezdxf.__version__}")
    except Exception as e:
        print(f"❌ ezdxf failed: {e}")
        return False
    
    return True

def test_vtk_import():
    """Test VTK import and basic functionality"""
    print("\n=== TESTING VTK IMPORT ===")
    try:
        import vtk
        print(f"✅ VTK {vtk.vtkVersion.GetVTKVersion()}")
        
        # Test basic VTK object creation
        sphere = vtk.vtkSphereSource()
        print("✅ VTK basic object creation")
        
        return True
    except Exception as e:
        print(f"❌ VTK failed: {e}")
        traceback.print_exc()
        return False

def test_vtkbool_import():
    """Test vtkbool import"""
    print("\n=== TESTING VTKBOOL IMPORT ===")
    try:
        from vtkbool.vtkBool import vtkPolyDataBooleanFilter
        print("✅ vtkbool import successful")
        return True
    except Exception as e:
        print(f"❌ vtkbool failed: {e}")
        traceback.print_exc()
        return False

def test_pyvista_import():
    """Test PyVista import without rendering"""
    print("\n=== TESTING PYVISTA IMPORT ===")
    try:
        import pyvista as pv
        print(f"✅ PyVista {pv.__version__}")
        
        # Test basic mesh creation (no rendering)
        sphere = pv.Sphere()
        print("✅ PyVista basic mesh creation")
        
        return True
    except Exception as e:
        print(f"❌ PyVista failed: {e}")
        traceback.print_exc()
        return False

def test_qt_import():
    """Test Qt import"""
    print("\n=== TESTING QT IMPORT ===")
    try:
        from PyQt5 import QtCore, QtWidgets
        print("✅ PyQt5 basic import")
        return True
    except Exception as e:
        print(f"❌ PyQt5 failed: {e}")
        traceback.print_exc()
        return False

def test_pyvistaqt_import():
    """Test PyVistaQt import (this often causes segfaults)"""
    print("\n=== TESTING PYVISTAQT IMPORT ===")
    try:
        # Set environment variables for headless operation
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        os.environ['DISPLAY'] = ':99'  # Dummy display
        
        from pyvistaqt import QtInteractor
        print("✅ PyVistaQt import successful")
        return True
    except Exception as e:
        print(f"❌ PyVistaQt failed: {e}")
        traceback.print_exc()
        return False

def test_generator_import():
    """Test haptic harness generator import"""
    print("\n=== TESTING GENERATOR IMPORT ===")
    try:
        from haptic_harness_generator.core.generator import Generator
        print("✅ Generator import successful")
        return True
    except Exception as e:
        print(f"❌ Generator import failed: {e}")
        traceback.print_exc()
        return False

def test_generator_creation():
    """Test generator object creation"""
    print("\n=== TESTING GENERATOR CREATION ===")
    try:
        import tempfile
        from haptic_harness_generator.core.generator import Generator
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = Generator(temp_dir)
            print("✅ Generator object creation successful")
            return True
    except Exception as e:
        print(f"❌ Generator creation failed: {e}")
        traceback.print_exc()
        return False

def test_headless_generation():
    """Test headless generation (no UI)"""
    print("\n=== TESTING HEADLESS GENERATION ===")
    try:
        import tempfile
        from haptic_harness_generator.core.generator import Generator
        
        # Set headless environment
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = Generator(temp_dir)
            # Try to generate just one component
            tyvek = generator.generateTyvekTile()
            print("✅ Headless generation successful")
            return True
    except Exception as e:
        print(f"❌ Headless generation failed: {e}")
        traceback.print_exc()
        return False

def check_system_info():
    """Check system information"""
    print("\n=== SYSTEM INFORMATION ===")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Conda env: {os.environ.get('CONDA_DEFAULT_ENV', 'NOT_IN_CONDA')}")
    
    # Check for display
    display = os.environ.get('DISPLAY', 'NOT_SET')
    print(f"DISPLAY: {display}")
    
    # Check for graphics libraries
    try:
        import subprocess
        result = subprocess.run(['glxinfo', '-B'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ OpenGL available")
            for line in result.stdout.split('\n')[:5]:
                if line.strip():
                    print(f"  {line}")
        else:
            print("❌ OpenGL not available or glxinfo failed")
    except:
        print("❌ Could not check OpenGL (glxinfo not available)")

def main():
    """Run all diagnostic tests"""
    print("HAPTIC HARNESS GENERATOR - SEGFAULT DIAGNOSTIC")
    print("=" * 50)
    
    check_system_info()
    
    tests = [
        test_basic_imports,
        test_vtk_import,
        test_vtkbool_import,
        test_pyvista_import,
        test_qt_import,
        test_pyvistaqt_import,
        test_generator_import,
        test_generator_creation,
        test_headless_generation,
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] Running {test.__name__}...")
        try:
            if not test():
                print(f"❌ Test {test.__name__} failed - stopping here")
                break
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            traceback.print_exc()
            break
        print(f"✅ Test {test.__name__} passed")
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC COMPLETE")
    print("If segfault occurs, it's likely in the last successful test or the next one.")

if __name__ == "__main__":
    main()
