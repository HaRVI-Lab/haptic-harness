#!/usr/bin/env python3
"""
Patch script to fix segmentation fault issues in the haptic harness generator.
This script modifies the main application to handle graphics initialization more robustly.
"""

import os
import sys
from pathlib import Path

def create_safe_main():
    """Create a safer version of main.py that handles graphics issues"""
    
    safe_main_content = '''import sys
import os
from PyQt5 import QtWidgets, QtCore
from haptic_harness_generator.ui.main_window import MyMainWindow
import argparse


def setup_safe_graphics():
    """Setup graphics environment safely"""
    # Try to detect if we're in a headless environment
    display = os.environ.get('DISPLAY', '')
    
    if not display or display == ':99':
        print("Detected headless environment, setting up offscreen rendering...")
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        os.environ['VTK_SILENCE_GET_VOID_POINTER_WARNINGS'] = '1'
        
        # Set PyVista to offscreen mode
        try:
            import pyvista as pv
            pv.OFF_SCREEN = True
            pv.set_plot_theme('document')
        except ImportError:
            pass
    
    # Set safe Qt attributes before QApplication creation
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    
    # Only set OpenGL sharing if we have a display
    if display and display != ':99':
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)


def check_environment():
    """Check that the environment is correctly set up"""
    errors = []

    # Check VTK version
    try:
        import vtk
        vtk_version = vtk.vtkVersion.GetVTKVersion()
        if vtk_version != "9.3.0":
            errors.append(f"Wrong VTK version: expected 9.3.0, got {vtk_version}")
    except ImportError:
        errors.append("VTK not installed")

    # Check vtkbool import
    try:
        from vtkbool.vtkBool import vtkPolyDataBooleanFilter
    except ImportError:
        errors.append("vtkbool import failed - check that vtkbool is installed correctly")

    # Check conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'NOT_IN_CONDA')
    if conda_env != 'hhgen':
        errors.append(f"Not in expected conda environment 'hhgen', currently in: {conda_env}")

    if errors:
        print("❌ ENVIRONMENT CHECK FAILED")
        print("The following issues were detected:")
        for error in errors:
            print(f"  - {error}")
        print("\\nTo fix these issues:")
        print("1. Remove current environment: conda remove -n hhgen --all")
        print("2. Create fresh environment: conda env create -f environment-locked.yml")
        print("3. Activate environment: conda activate hhgen")
        print("4. Install package: pip install -e .")
        print("5. Run environment verification: python verify_environment.py")
        
        # Suggest headless mode for graphics issues
        print("\\nIf you're experiencing segmentation faults:")
        print("6. Try headless mode: python run_headless.py --export-dir /path/to/output")
        print("7. Or run diagnostics: python diagnose_segfault.py")
        
        sys.exit(1)

    print("✅ Environment check passed")


def run_app():
    # Check environment before starting
    check_environment()
    
    # Setup safe graphics environment
    setup_safe_graphics()

    parser = argparse.ArgumentParser(description="Haptic Harness Generator")
    parser.add_argument(
        "--export-dir",
        help="Absolute path to export files to",
        default=None,
        required=True,
    )
    parser.add_argument(
        "--headless",
        help="Run in headless mode (no GUI)",
        action="store_true"
    )
    
    args = parser.parse_args()
    export_dir = os.path.abspath(args.export_dir)
    
    if not os.path.isabs(export_dir):
        print(f"Error: Please provide an absolute path. Converted path: {export_dir}")
        print(
            "You can use an absolute path like: /home/user/exports or C:\\\\Users\\\\YourName\\\\exports"
        )
        sys.exit(1)

    try:
        os.makedirs(export_dir, exist_ok=True)
        print(f"Files will be exported to: {export_dir}")
    except OSError as e:
        print(f"Error creating directory {export_dir}: {e}")
        sys.exit(1)

    if args.headless:
        print("Running in headless mode...")
        # Import and run headless version
        try:
            from run_headless import generate_preset
            generate_preset("Standard 4-sided", export_dir)
            print("✅ Headless generation completed successfully")
            return
        except Exception as e:
            print(f"❌ Headless generation failed: {e}")
            sys.exit(1)

    print("The software may take a minute before startup...")

    try:
        app = QtWidgets.QApplication(sys.argv)
        
        # Test if we can create the main window safely
        try:
            window = MyMainWindow(userDir=export_dir)
            sys.exit(app.exec_())
        except Exception as e:
            print(f"❌ GUI initialization failed: {e}")
            print("\\nTrying fallback to headless mode...")
            
            # Fallback to headless mode
            try:
                from run_headless import generate_preset
                generate_preset("Standard 4-sided", export_dir)
                print("✅ Fallback headless generation completed successfully")
            except Exception as e2:
                print(f"❌ Fallback headless generation also failed: {e2}")
                print("\\nPlease run diagnostics: python diagnose_segfault.py")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        print("\\nTrying headless mode as fallback...")
        
        try:
            from run_headless import generate_preset
            generate_preset("Standard 4-sided", export_dir)
            print("✅ Headless fallback completed successfully")
        except Exception as e2:
            print(f"❌ All modes failed: {e2}")
            print("\\nPlease run diagnostics: python diagnose_segfault.py")
            sys.exit(1)


if __name__ == "__main__":
    run_app()
'''
    
    return safe_main_content

def backup_original_main():
    """Backup the original main.py"""
    main_path = Path("haptic_harness_generator/main.py")
    backup_path = Path("haptic_harness_generator/main.py.backup")
    
    if main_path.exists() and not backup_path.exists():
        import shutil
        shutil.copy2(main_path, backup_path)
        print(f"✅ Backed up original main.py to {backup_path}")
    elif backup_path.exists():
        print(f"✅ Backup already exists at {backup_path}")
    else:
        print(f"❌ Could not find {main_path}")
        return False
    
    return True

def apply_fix():
    """Apply the segfault fix"""
    print("APPLYING SEGFAULT FIX")
    print("=" * 30)
    
    # Backup original
    if not backup_original_main():
        return False
    
    # Create safe version
    safe_content = create_safe_main()
    main_path = Path("haptic_harness_generator/main.py")
    
    try:
        with open(main_path, 'w') as f:
            f.write(safe_content)
        print(f"✅ Applied fix to {main_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to apply fix: {e}")
        return False

def restore_original():
    """Restore the original main.py"""
    main_path = Path("haptic_harness_generator/main.py")
    backup_path = Path("haptic_harness_generator/main.py.backup")
    
    if backup_path.exists():
        import shutil
        shutil.copy2(backup_path, main_path)
        print(f"✅ Restored original main.py from backup")
        return True
    else:
        print(f"❌ No backup found at {backup_path}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_original()
    else:
        apply_fix()
        print("\\nFix applied! Now try running:")
        print("1. python diagnose_segfault.py  # To diagnose the issue")
        print("2. python run_headless.py --export-dir /tmp/test  # For headless mode")
        print("3. run-haptic-harness --export-dir /tmp/test  # Normal mode with fallback")
        print("4. run-haptic-harness --export-dir /tmp/test --headless  # Force headless")

if __name__ == "__main__":
    main()
