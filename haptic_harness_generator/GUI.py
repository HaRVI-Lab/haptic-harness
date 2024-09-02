from pyvistaqt import QtInteractor, MainWindow
from PyQt5 import QtCore, QtWidgets, Qt
import sys
from .Styles import Styles
from .Generator import Generator
import re


class MyMainWindow(MainWindow):

    def __init__(self, parent=None, show=True):
        QtWidgets.QMainWindow.__init__(self, parent)

        styleSheet = Styles()
        app.setStyleSheet(styleSheet.getStyles())
        self.interactorColor = styleSheet.colors["green"]
        primaryLayout = Qt.QHBoxLayout()
        self.frame = QtWidgets.QFrame()
        self.plotters = []
        self.generator = Generator()

        tabs = Qt.QTabWidget()
        tabs.addTab(self.initInstructionsTab(), "Instructions")
        tabs.addTab(self.initTileTab(), "Generate Tiles")
        tabs.addTab(self.initPeripheralsTab(), "Generate Peripherals")
        # tabs.setFixedWidth(600)
        primaryLayout.addWidget(tabs)

        # self.setCentralWidget(self.frame)

        centralWidget = Qt.QWidget(objectName="totalBackground")
        centralWidget.setLayout(primaryLayout)
        self.setCentralWidget(centralWidget)

        if show:
            self.show()

    def initTileTab(self):
        tab = Qt.QWidget()
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

        self.entryBox = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()

        attributes = self.generator.__dict__
        for attributeKey, attributeVal in attributes.items():
            hbox = QtWidgets.QHBoxLayout()
            formattedAttributeName = re.sub(
                r"(?<!^)(?=[A-Z])", " ", attributeKey
            ).title()
            label = QtWidgets.QLabel(formattedAttributeName)
            spin_box = QtWidgets.QSpinBox()
            # TODO: change int qspinbox
            spin_box.setValue(int(attributeVal))
            spin_box.textChanged.connect(
                lambda value, attributeKey=attributeKey: self.setGeneratorAttribute(
                    attributeKey, value
                )
            )
            hbox.addWidget(label)
            hbox.addWidget(spin_box)
            vbox.addLayout(hbox)

        regen = QtWidgets.QPushButton("Generate Parts")
        vbox.addWidget(regen)
        regen.clicked.connect(self.regen)

        self.entryBox.setLayout(vbox)
        hbox_layout = QtWidgets.QHBoxLayout()
        hbox_layout.addWidget(self.entryBox)
        frame = Qt.QFrame(objectName="sectionFrame")
        frame.setFrameShape(Qt.QFrame.StyledPanel)
        frame.setLayout(interactors_layout)
        hbox_layout.addWidget(frame)
        tab.setLayout(hbox_layout)
        return tab

    def initPeripheralsTab(self):
        tab = Qt.QWidget()
        layout = Qt.QVBoxLayout()
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

        layout.addLayout(plotLayout)
        regenPeripherals = QtWidgets.QPushButton("Generate Parts")
        layout.addWidget(regenPeripherals)
        regenPeripherals.clicked.connect(self.regenPeripherals)
        tab.setLayout(layout)

        return tab

    def initInstructionsTab(self):
        tab = Qt.QWidget()
        layout = Qt.QHBoxLayout()
        label = QtWidgets.QLabel()
        label.setAlignment(QtCore.Qt.AlignLeft)
        layout.addWidget(label)
        label.setText(
            """
        <html>
            <h1>How to use the haptic harness generator:</h1>
            <p>Navigate the software by switching between the "Tile Generator", "Peripherals Generator", and "Instructions" tabs at the top of the program.</p>
            <h3>Using the "Tile Generator" tab:</h3>
            <ul>
                <li>This portion of the software generates the tyvek, foam, and magnetic ring components of a haptic harness tile</li>
                <li>The 1st quadrant displays the magnetic ring</li>
                <li>The 2nd quadrant displays the tyvek tile</li>
                <li>The 3rd quadrant displays the foam backing</li>
                <li>Use the 4th quadrant to change the tile parameters</li>
                <ul>
                    <li>Change parameters then click the "Generate Parts" button to generate the .dxf files for each component</li>
                </ul>
            </ul>
            <h3>Using the "Peripheral Generator" tab:</h3>
        </html>
                      """
        )
        tab.setLayout(layout)
        return tab

    def setGeneratorAttribute(self, attrName, val):
        self.generator.customSetAttr(attrName=attrName, val=val)

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


app = QtWidgets.QApplication(sys.argv)
window = MyMainWindow()
sys.exit(app.exec_())
