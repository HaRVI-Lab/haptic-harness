#!/usr/bin/env python3
"""
Migration script to detect and remove old installations of haptic-harness-generator.
This script helps users transition from PyPI installations to the new conda-based approach.
"""

import subprocess
import sys
import os
import importlib.util

def run_command(cmd, check=False):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return None

def check_pypi_installation():
    """Check if haptic-harness-generator is installed via pip"""
    print("Checking for PyPI installation...")
    
    result = run_command("pip list | grep haptic-harness-generator")
    if result and result.returncode == 0 and result.stdout.strip():
        print("⚠️  Found PyPI installation of haptic-harness-generator")
        return True
    
    # Also check with pip show
    result = run_command("pip show haptic-harness-generator")
    if result and result.returncode == 0:
        print("⚠️  Found PyPI installation of haptic-harness-generator")
        return True
    
    print("✅ No PyPI installation found")
    return False

def check_environment_compatibility():
    """Check if current environment is compatible"""
    print("\nChecking environment compatibility...")
    
    # Check if we're in the right conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'NOT_IN_CONDA')
    if conda_env != 'hhgen':
        print(f"⚠️  Not in expected conda environment 'hhgen', currently in: {conda_env}")
        return False
    
    # Check VTK version
    try:
        import vtk
        vtk_version = vtk.vtkVersion.GetVTKVersion()
        if vtk_version != "9.3.0":
            print(f"⚠️  Wrong VTK version: expected 9.3.0, got {vtk_version}")
            return False
        print(f"✅ VTK version correct: {vtk_version}")
    except ImportError:
        print("❌ VTK not installed")
        return False
    
    # Check vtkbool import
    try:
        from vtkbool.vtkBool import vtkPolyDataBooleanFilter
        print("✅ vtkbool import working correctly")
    except ImportError:
        print("❌ vtkbool import failed")
        return False
    
    return True

def remove_pypi_installation():
    """Remove PyPI installation of haptic-harness-generator"""
    print("\nRemoving PyPI installation...")
    
    result = run_command("pip uninstall haptic-harness-generator -y")
    if result and result.returncode == 0:
        print("✅ PyPI installation removed successfully")
        return True
    else:
        print("❌ Failed to remove PyPI installation")
        if result:
            print(f"Error: {result.stderr}")
        return False

def detect_installation_issues():
    """Detect common installation issues"""
    issues = []
    
    # Check for multiple Python environments
    result = run_command("conda env list | grep hhgen")
    if result and result.returncode == 0:
        env_count = len([line for line in result.stdout.split('\n') if 'hhgen' in line])
        if env_count > 1:
            issues.append("Multiple hhgen environments detected")
    
    # Check for conflicting packages
    try:
        import pkg_resources
        installed_packages = [d.project_name for d in pkg_resources.working_set]
        
        conflicts = []
        if 'haptic-harness-generator' in installed_packages:
            conflicts.append('haptic-harness-generator (PyPI version)')
        
        if conflicts:
            issues.append(f"Conflicting packages: {', '.join(conflicts)}")
    except:
        pass
    
    return issues

def main():
    """Main migration function"""
    print("="*60)
    print("HAPTIC HARNESS GENERATOR - INSTALLATION MIGRATION")
    print("="*60)
    
    # Check for PyPI installation
    has_pypi = check_pypi_installation()
    
    # Check environment compatibility
    env_compatible = check_environment_compatibility()
    
    # Detect other issues
    issues = detect_installation_issues()
    
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    
    if has_pypi:
        print("❌ PyPI installation detected - needs removal")
        response = input("Remove PyPI installation? (y/N): ")
        if response.lower() in ['y', 'yes']:
            if remove_pypi_installation():
                print("✅ PyPI installation removed")
            else:
                print("❌ Failed to remove PyPI installation")
                return False
        else:
            print("⚠️  PyPI installation left intact - may cause conflicts")
    
    if not env_compatible:
        print("❌ Environment incompatible")
        print("\nTo fix environment issues:")
        print("1. Remove current environment: conda remove -n hhgen --all")
        print("2. Create fresh environment: conda env create -f environment-locked.yml")
        print("3. Activate environment: conda activate hhgen")
        print("4. Install package: pip install -e .")
        return False
    
    if issues:
        print("⚠️  Issues detected:")
        for issue in issues:
            print(f"   - {issue}")
    
    if not has_pypi and env_compatible and not issues:
        print("✅ Installation is clean and compatible")
        print("No migration needed!")
        return True
    
    print("\nRun this script again after fixing issues to verify the installation.")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
