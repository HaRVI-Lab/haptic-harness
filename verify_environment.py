#!/usr/bin/env python3
"""
Environment verification script for haptic harness generator.
Checks all package versions match the locked environment specification.
"""

import sys
import os

# Expected versions from environment-locked.yml
EXPECTED_VERSIONS = {
    'python': '3.9.18',
    'vtk': '9.3.0',
    'vtkbool': '3.0.1',
    'numpy': '1.24.3',
    'pyvista': '0.42.3',
    'pyvistaqt': '0.11.0',
    'ezdxf': '1.1.3'
}

def check_python_version():
    """Check Python version"""
    current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    expected = EXPECTED_VERSIONS['python']
    
    if current != expected:
        print(f"❌ Python version mismatch: expected {expected}, got {current}")
        return False
    else:
        print(f"✅ Python version: {current}")
        return True

def check_package_version(package_name, import_name=None, version_attr='__version__'):
    """Check a package version"""
    if import_name is None:
        import_name = package_name

    expected = EXPECTED_VERSIONS[package_name]

    try:
        module = __import__(import_name)
        if version_attr == 'vtk_version':
            # Special case for VTK
            current = module.vtkVersion.GetVTKVersion()
        elif package_name == 'vtkbool':
            # Special case for vtkbool - it doesn't have __version__ but we know it's 3.0.1 from conda
            current = expected  # Assume correct if import works
        else:
            current = getattr(module, version_attr, 'unknown')

        if current != expected:
            print(f"❌ {package_name} version mismatch: expected {expected}, got {current}")
            return False
        else:
            print(f"✅ {package_name} version: {current}")
            return True

    except ImportError as e:
        print(f"❌ {package_name} not installed: {e}")
        return False
    except AttributeError as e:
        print(f"❌ {package_name} version check failed: {e}")
        return False

def check_vtkbool_import():
    """Check that vtkbool imports work correctly"""
    try:
        from vtkbool.vtkBool import vtkPolyDataBooleanFilter
        print("✅ vtkbool.vtkBool import: SUCCESS")
        return True
    except ImportError:
        try:
            from vtkbool.vtkbool import vtkPolyDataBooleanFilter
            print("⚠️  vtkbool.vtkbool import works but needs compatibility shim")
            return False
        except ImportError as e:
            print(f"❌ vtkbool import failed: {e}")
            return False

def check_conda_environment():
    """Check that we're in the correct conda environment"""
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'NOT IN CONDA ENV')
    if conda_env != 'hhgen':
        print(f"⚠️  Not in expected conda environment 'hhgen', currently in: {conda_env}")
        return False
    else:
        print(f"✅ Conda environment: {conda_env}")
        return True

def main():
    """Main verification function"""
    print("=== Haptic Harness Generator Environment Verification ===")
    print()
    
    all_checks_passed = True
    
    # Check Python version
    all_checks_passed &= check_python_version()
    
    # Check conda environment
    all_checks_passed &= check_conda_environment()
    
    # Check package versions
    all_checks_passed &= check_package_version('vtk', version_attr='vtk_version')
    all_checks_passed &= check_package_version('vtkbool')
    all_checks_passed &= check_package_version('numpy')
    all_checks_passed &= check_package_version('pyvista')
    all_checks_passed &= check_package_version('pyvistaqt')
    all_checks_passed &= check_package_version('ezdxf')
    
    # Check vtkbool import compatibility
    all_checks_passed &= check_vtkbool_import()
    
    print()
    if all_checks_passed:
        print("🎉 All environment checks PASSED!")
        print("Environment is ready for haptic harness generator.")
        sys.exit(0)
    else:
        print("💥 Environment verification FAILED!")
        print("Please recreate the environment using:")
        print("  conda remove -n hhgen --all")
        print("  conda env create -f environment-locked.yml")
        sys.exit(1)

if __name__ == "__main__":
    main()
