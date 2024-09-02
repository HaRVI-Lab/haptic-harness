import sys
from PyQt5 import QtWidgets
from .GUI import MyMainWindow
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
export_dir = os.path.join(base_dir, "..", "exports")
if not os.path.exists(export_dir):
    os.makedirs(export_dir)


def run_app():
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    sys.exit(app.exec_())
