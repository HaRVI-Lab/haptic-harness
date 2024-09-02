import sys
from PyQt5 import QtWidgets
from .GUI import MyMainWindow
import os
import argparse


def run_app():
    parser = argparse.ArgumentParser(description="Haptic Harness Generator")
    parser.add_argument(
        "--export-dir",
        help="Absolute path to export files to",
        default=None,
        required=True,
    )
    args = parser.parse_args()
    export_dir = os.path.abspath(args.export_dir)
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
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow(userDir=export_dir)
    sys.exit(app.exec_())
