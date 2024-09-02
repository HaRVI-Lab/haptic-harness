import sys
from PyQt5 import QtWidgets
from .GUI import MyMainWindow


def run_app():
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    sys.exit(app.exec_())
