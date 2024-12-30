from pyvistaqt import QtInteractor, MainWindow
from PyQt5 import QtCore, QtWidgets, Qt, QtGui, QtWebEngineWidgets
from .Styles import Styles
from .Generator import Generator
import re
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
instructions_file_path = os.path.join(current_dir, "instructions.html")


class MyMainWindow(MainWindow):

    def __init__(self, userDir, parent=None, show=True):
        QtWidgets.QMainWindow.__init__(self, parent)

        styleSheet = Styles()
        super().setStyleSheet(styleSheet.getStyles())
        self.interactorColor = styleSheet.colors["green"]
        primaryLayout = Qt.QHBoxLayout()
        self.frame = QtWidgets.QFrame()
        self.plotters = []
        self.generator = Generator(userDir)
        self.dataValidationCheckBox = QtWidgets.QCheckBox("Data Validation", self)
        self.dataValidationCheckBox.setChecked(True)
        self.dataValidationCheckBox.clicked.connect(self.setDataValidation)

        tab = Qt.QWidget()
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.paramtersPane())
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.initTilePane())
        vbox.addWidget(self.initPeripheralsPane())
        hbox.addLayout(vbox)
        tab.setLayout(hbox)

        tabs = Qt.QTabWidget()
        tabs.addTab(tab, "Generate Tiles")
        tabs.addTab(self.initInstructions(), "Instructions")
        primaryLayout.addWidget(tabs)

        centralWidget = Qt.QWidget(objectName="totalBackground")
        centralWidget.setLayout(primaryLayout)
        self.setCentralWidget(centralWidget)

        if show:
            self.show()

    def initInstructions(self):
        view = QtWebEngineWidgets.QWebEngineView()
        with open(instructions_file_path, "r") as instructions_file:
            view.setHtml(instructions_file.read())
        return view

    def paramtersPane(self):
        self.entryBox = QtWidgets.QScrollArea()
        scroll = QtWidgets.QWidget()

        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(20, 20, 40, 20)

        vbox.addWidget(self.dataValidationCheckBox)

        attributes = self.generator.__dict__
        for attributeKey, attributeVal in attributes.items():
            if attributeKey == "userDir":
                continue
            hbox = QtWidgets.QHBoxLayout()
            formattedAttributeName = re.sub(
                r"(?<!^)(?=[A-Z])", " ", attributeKey
            ).title()
            label = QtWidgets.QLabel(formattedAttributeName)
            if attributeKey == "numSides" or attributeKey == "numMagnetsInRing":
                le = QtWidgets.QLineEdit()
                le.setValidator(
                    QtGui.QRegularExpressionValidator(
                        QtCore.QRegularExpression("^\d+$")
                    )
                )
                le.setText(str(attributeVal))
            else:
                le = QtWidgets.QLineEdit()
                le.setValidator(
                    QtGui.QRegularExpressionValidator(
                        QtCore.QRegularExpression("^\d+(\.\d+)?$")
                    )
                )
                le.setText(str(attributeVal))
            le.textChanged.connect(
                lambda value, attributeKey=attributeKey: self.setGeneratorAttribute(
                    attributeKey, value
                )
            )
            hbox.addWidget(label)
            hbox.addWidget(le)
            vbox.addLayout(hbox)

        regen = QtWidgets.QPushButton("Generate Parts")
        vbox.addWidget(regen)
        label = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("haptic_harness_generator/anatomyOfTile.jpg")
        scaled_pixmap = pixmap.scaledToWidth(
            self.entryBox.width(), mode=QtCore.Qt.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)
        vbox.addWidget(label)
        regen.clicked.connect(self.regenParts)

        scroll.setLayout(vbox)
        self.entryBox.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.entryBox.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.entryBox.setWidgetResizable(True)
        self.entryBox.setWidget(scroll)
        self.entryBox.setFixedWidth(scroll.width())
        return self.entryBox

    def initTilePane(self):
        interactors_layout = QtWidgets.QHBoxLayout()
        labels = ["Tyvek Tile", "Foam Liner", "Magnetic Ring"]
        for i in range(3):
            section = QtWidgets.QVBoxLayout()
            self.plotters.append(QtInteractor(self.frame))
            label = QtWidgets.QLabel(labels[i], objectName="sectionHeader")
            label.setAlignment(QtCore.Qt.AlignCenter)
            section.addWidget(label)
            section.addWidget(self.plotters[i].interactor)
            frame = Qt.QFrame(objectName="sectionFrame")
            frame.setFrameShape(Qt.QFrame.StyledPanel)
            frame.setLayout(section)
            interactors_layout.addWidget(frame)

        self.plotters[0].add_mesh(
            self.generator.generateTyvekTile(),
            show_edges=True,
            line_width=3,
            color=self.interactorColor,
        )
        self.plotters[1].add_mesh(
            self.generator.generateFoam(),
            show_edges=True,
            line_width=3,
            color=self.interactorColor,
        )
        self.plotters[2].add_mesh(
            self.generator.generateMagnetRing(),
            show_edges=True,
            line_width=3,
            color=self.interactorColor,
        )

        frame = Qt.QFrame(objectName="sectionFrame")
        frame.setFrameShape(Qt.QFrame.StyledPanel)
        frame.setLayout(interactors_layout)
        return frame

    def initPeripheralsPane(self):
        plotLayout = Qt.QHBoxLayout()

        section = QtWidgets.QVBoxLayout()
        self.plotters.append(QtInteractor(self.frame))
        label = QtWidgets.QLabel("Base", objectName="sectionHeader")
        label.setAlignment(QtCore.Qt.AlignCenter)
        section.addWidget(label)
        section.addWidget(self.plotters[3].interactor)
        frame = Qt.QFrame(objectName="sectionFrame")
        frame.setFrameShape(Qt.QFrame.StyledPanel)
        frame.setLayout(section)
        plotLayout.addWidget(frame)
        self.plotters[3].add_mesh(
            self.generator.generateBase(), color=self.interactorColor
        )

        section = QtWidgets.QVBoxLayout()
        self.plotters.append(QtInteractor(self.frame))
        label = QtWidgets.QLabel("Bottom Clip", objectName="sectionHeader")
        label.setAlignment(QtCore.Qt.AlignCenter)
        section.addWidget(label)
        section.addWidget(self.plotters[4].interactor)
        frame = Qt.QFrame(objectName="sectionFrame")
        frame.setFrameShape(Qt.QFrame.StyledPanel)
        frame.setLayout(section)
        plotLayout.addWidget(frame)
        self.plotters[4].add_mesh(
            self.generator.generateBottomClip(), color=self.interactorColor
        )

        section = QtWidgets.QVBoxLayout()
        self.plotters.append(QtInteractor(self.frame))
        label = QtWidgets.QLabel("Top Clip", objectName="sectionHeader")
        label.setAlignment(QtCore.Qt.AlignCenter)
        section.addWidget(label)
        section.addWidget(self.plotters[5].interactor)
        frame = Qt.QFrame(objectName="sectionFrame")
        frame.setFrameShape(Qt.QFrame.StyledPanel)
        frame.setLayout(section)
        plotLayout.addWidget(frame)
        self.plotters[5].add_mesh(
            self.generator.generateTopClip(), color=self.interactorColor
        )

        frame = Qt.QFrame(objectName="sectionFrame")
        frame.setFrameShape(Qt.QFrame.StyledPanel)
        frame.setLayout(plotLayout)
        return frame

    def setGeneratorAttribute(self, attrName, val):
        self.generator.customSetAttr(attrName=attrName, val=val)

    def setDataValidation(self, state):
        if not self.dataValidationCheckBox.isChecked():
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText(
                "Turning off data validation may lead to incompatible geometry, which may crash the program"
            )
            msg.setWindowTitle("Validation Error")
            msg.setStandardButtons(
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
            )
            retval = msg.exec_()
            if retval == QtWidgets.QMessageBox.Ok:
                self.dataValidationCheckBox.setChecked(False)
            elif retval == QtWidgets.QMessageBox.Cancel:
                self.dataValidationCheckBox.setChecked(True)

    def regenParts(self):
        messages = []
        if self.dataValidationCheckBox.isChecked():
            messages = self.generator.validate()
        if len(messages) == 0:
            self.regen()
            self.regenPeripherals()
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("\n\n".join(messages))
            msg.setWindowTitle("Validation Error")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            retval = msg.exec_()

    def regen(self):
        self.plotters[0].clear_actors()
        self.plotters[0].add_mesh(
            self.generator.generateTyvekTile(),
            show_edges=True,
            line_width=3,
            color=self.interactorColor,
        )
        self.plotters[1].clear_actors()
        self.plotters[1].add_mesh(
            self.generator.generateFoam(),
            show_edges=True,
            line_width=3,
            color=self.interactorColor,
        )
        self.plotters[2].clear_actors()
        self.plotters[2].add_mesh(
            self.generator.generateMagnetRing(),
            show_edges=True,
            line_width=3,
            color=self.interactorColor,
        )

    def regenPeripherals(self):
        self.plotters[3].clear_actors()
        self.plotters[3].add_mesh(
            self.generator.generateBase(), color=self.interactorColor
        )

        self.plotters[4].clear_actors()
        self.plotters[4].add_mesh(
            self.generator.generateBottomClip(), color=self.interactorColor
        )

        self.plotters[5].clear_actors()
        self.plotters[5].add_mesh(
            self.generator.generateTopClip(), color=self.interactorColor
        )
