import sys
from PyQt5 import QtWidgets, QtCore
from haptic_harness_generator.ui.main_window import MyMainWindow
import os
import argparse


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
        print("\nTo fix these issues:")
        print("1. Remove current environment: conda remove -n hhgen --all")
        print("2. Create fresh environment: conda env create -f environment-locked.yml")
        print("3. Activate environment: conda activate hhgen")
        print("4. Install package: pip install -e .")
        print("5. Run environment verification: python verify_environment.py")
        sys.exit(1)

    print("✅ Environment check passed")

def run_app():
    # Check environment before starting
    check_environment()

    parser = argparse.ArgumentParser(description="Haptic Harness Generator")
    parser.add_argument(
        "--export-dir",
        help="Absolute path to export files to",
        default=None,
        required=True,
    )
    args = parser.parse_args()
    export_dir = os.path.abspath(args.export_dir)
    print(export_dir)
    if not os.path.isabs(export_dir):
        print(f"Error: Please provide an absolute path. Converted path: {export_dir}")
        print(
            "You can use an absolute path like: /home/user/exports or C:\\Users\\YourName\\exports"
        )
        sys.exit(1)

    try:
        os.makedirs(export_dir, exist_ok=True)
        print(f"Files will be exported to: {export_dir}")
    except OSError as e:
        print(f"Error creating directory {export_dir}: {e}")
        sys.exit(1)

    print("The software may take a minute before startup...")

    # Enable high DPI scaling and WebEngine support before creating QApplication
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)

    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow(userDir=export_dir)
    sys.exit(app.exec_())
