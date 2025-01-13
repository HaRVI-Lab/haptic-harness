from pyvistaqt import QtInteractor, MainWindow
from PyQt5 import QtCore, QtWidgets, Qt, QtGui, QtWebEngineWidgets
from .Styles import Styles
from .Generator import Generator, WorkerWrapper
from time import perf_counter
import re
import os
from pyvista import Camera

current_dir = os.path.dirname(os.path.abspath(__file__))
rotate_icon_path = os.path.join(current_dir, "rotateIcon.png")
anatomy_of_tile_path = os.path.join(current_dir, "haptics.jpg")


class MyMainWindow(MainWindow):

    def __init__(self, userDir, parent=None, show=True):
        QtWidgets.QMainWindow.__init__(self, parent)

        styleSheet = Styles()
        super().setStyleSheet(styleSheet.getStyles())
        self.interactorColor = styleSheet.colors["green"]
        self.grayColor = styleSheet.colors["lightGray"]
        primaryLayout = Qt.QHBoxLayout()
        self.frame = QtWidgets.QFrame()
        self.plotters = []
        self.regen_button = QtWidgets.QPushButton("Generate Parts")
        self.regen_button.clicked.connect(self.regen)
        self.pbar = QtWidgets.QProgressBar(self)
        self.pbar.setFormat("Initialized")
        self.pbar.setValue(100)
        self.generator = Generator(userDir)
        self.generator.signals.progress.connect(self.update_progress)
        self.generator.signals.finished.connect(self.task_finished)
        self.threadpool = QtCore.QThreadPool()
        self.dataValidationCheckBox = QtWidgets.QCheckBox("Data Validation", self)
        self.dataValidationCheckBox.setChecked(True)
        self.dataValidationCheckBox.clicked.connect(self.setDataValidation)

        primaryLayout.addWidget(self.paramtersPane())
        primaryLayout.addWidget(self.objectsPane(), stretch=4)

        centralWidget = Qt.QWidget(objectName="totalBackground")
        centralWidget.setLayout(primaryLayout)
        self.setCentralWidget(centralWidget)

        if show:
            self.show()

    def objectsPane(self):
        scroll_area = QtWidgets.QScrollArea()
        temp = QtWidgets.QWidget()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.pbar)
        vbox.addWidget(self.initTilePane())
        vbox.addWidget(self.initPeripheralsPane())
        self.settings = []
        for pl in self.plotters[:3]:
            pl.camera_position = "yx"
        for pl in self.plotters[3:]:
            self.settings.append(pl.camera.copy())
        reset_view = QtWidgets.QPushButton("Reset View")
        reset_view.clicked.connect(self.reset_view)
        vbox.addWidget(reset_view)

        temp.setLayout(vbox)

        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(temp)
        return scroll_area

    def paramtersPane(self):
        self.entryBox = QtWidgets.QScrollArea()
        scroll = QtWidgets.QWidget()

        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(20, 20, 40, 20)

        attributes = self.generator.__dict__
        parameter_attributes = {
            "Tile Parameters": [
                "concentricPolygonRadius",
                "tactorRadius",
                "magnetRingRadius",
                "numSides",
                "foamThickness",
                "distanceBetweenMagnetClipAndPolygonEdge",
                "numMangetsInRing",
            ],
            "Magnet Parameters": [
                "magnetRadius",
                "magnetThickness",
            ],
            "Clip Parameters": [
                "slotWidth",
                "slotHeight",
                "slotBorderRadius",
                "magnetClipThickness",
                "magnetClipRingThickness",
                "distanceBetweenMagnetsInClip",
                "distanceBetweenMagnetClipAndSlot",
            ],
            "Mount Parameters": [
                "mountRadius",
                "mountHeight",
                "mountShellThickness",
                "mountBottomAngleOpening",
                "mountTopAngleOpening",
                "brim",
            ],
        }

        unitless = ["numMangetsInRing", "numSides"]
        radians = ["mountBottomAngleOpening", "mountTopAngleOpening"]
        for header, params in parameter_attributes.items():
            temp_box = QtWidgets.QVBoxLayout()
            temp_box.setAlignment(QtCore.Qt.AlignVCenter)
            header = QtWidgets.QLabel(header, objectName="parameterHeader")
            header.setAlignment(QtCore.Qt.AlignLeft)
            temp_box.addWidget(header)
            for attributeKey in params:
                attributeVal = attributes[attributeKey]
                hbox = QtWidgets.QHBoxLayout()
                formattedAttributeName = re.sub(
                    r"(?<!^)(?=[A-Z])", " ", attributeKey
                ).title()
                if attributeKey in radians:
                    formattedAttributeName += " (radians)"
                elif attributeKey in unitless:
                    pass
                else:
                    formattedAttributeName += " (mm)"
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
                temp_box.addLayout(hbox)
            vbox.addLayout(temp_box)

        vbox.addWidget(self.dataValidationCheckBox)
        vbox.addWidget(self.regen_button)

        label = QtWidgets.QLabel(
            '<a href="https://github.com/HaRVI-Lab/haptic-harness" style="color: #339955; font-size: 16px;">Instructions on GitHub</a>'
        )
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setOpenExternalLinks(True)
        vbox.addWidget(label)

        label = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap(anatomy_of_tile_path)
        pixmap.setDevicePixelRatio(2.0)
        scaled_pixmap = pixmap.scaledToWidth(
            self.entryBox.width() * 2, mode=QtCore.Qt.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)
        vbox.addWidget(label)

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
            interactor = QtInteractor(self.frame)
            interactor.disable()
            interactor.interactor.setMinimumHeight(200)
            self.plotters.append(interactor)
            label = QtWidgets.QLabel(labels[i], objectName="sectionHeader")
            label.setAlignment(QtCore.Qt.AlignCenter)
            section.addWidget(label)
            section.addWidget(self.plotters[i].interactor)
            frame = Qt.QFrame(objectName="sectionFrame")
            frame.setFrameShape(Qt.QFrame.StyledPanel)
            frame.setLayout(section)
            interactors_layout.addWidget(frame)

        self.plotters[0].add_mesh(
            self.generator.tyvek_tile,
            show_edges=True,
            line_width=3,
            color=self.interactorColor,
        )
        self.plotters[1].add_mesh(
            self.generator.foam,
            show_edges=True,
            line_width=3,
            color=self.interactorColor,
        )
        self.plotters[2].add_mesh(
            self.generator.magnet_ring,
            show_edges=True,
            line_width=3,
            color=self.interactorColor,
        )

        frame = Qt.QFrame(objectName="sectionFrame")
        frame.setFrameShape(Qt.QFrame.StyledPanel)
        frame.setLayout(interactors_layout)
        return frame

    def reset_view(self):
        # 2D tile components
        centers = [
            self.generator.tyvek_tile.center,
            self.generator.foam.center,
            self.generator.magnet_ring.center,
        ]
        bounds = self.generator.tyvek_tile.bounds
        for i in range(3):
            self.plotters[i].camera.focal_point = centers[i]
            max_extent = max(
                bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]
            )
            distance = max_extent * 2.5
            self.plotters[i].camera.position = (
                centers[i][0],
                centers[i][1],
                centers[i][2] + distance,
            )
        # 3D peripherals
        for i in range(4):
            self.plotters[i + 3].camera = self.settings[i].copy()

    def initPeripheralsPane(self):

        plotLayout = Qt.QVBoxLayout()
        subPlotLayout = Qt.QHBoxLayout()

        labels = ["Base", "Bottom Clip", "Top Clip", "Mount"]

        for i in range(2):
            subPlotLayout = Qt.QHBoxLayout()
            for j in range(2):
                section = QtWidgets.QVBoxLayout()
                interactor = QtInteractor(self.frame)
                self.plotters.append(interactor)
                label = QtWidgets.QLabel(labels[i * 2 + j], objectName="sectionHeader")
                label.setAlignment(QtCore.Qt.AlignCenter)
                section.addWidget(label)
                section.addWidget(self.plotters[-1].interactor)
                frame = Qt.QFrame(objectName="sectionFrame")
                frame.setFrameShape(Qt.QFrame.StyledPanel)
                frame.setLayout(section)
                subPlotLayout.addWidget(frame)
                self.plotters[-1].add_mesh(
                    self.generator.generatedObjects[i * 2 + j + 3],
                    color=self.interactorColor,
                )
                self.plotters[-1].add_logo_widget(
                    rotate_icon_path,
                    position=(0.05, 0.05),
                    size=(0.1, 0.1),
                )
            plotLayout.addLayout(subPlotLayout)

        frame = Qt.QFrame(objectName="sectionFrame")
        frame.setFrameShape(Qt.QFrame.StyledPanel)
        frame.setLayout(plotLayout)

        return frame

    def setGeneratorAttribute(self, attrName, val):
        self.generator.customSetAttr(attrName=attrName, val=val)
        self.grayOutPlotters()
        self.pbar.setValue(0)
        self.pbar.setFormat("Ready to Generate")

    def grayOutPlotters(self):
        opacity = 0.7
        for i, pl in enumerate(self.plotters[:3]):
            pl.clear_actors()
            pl.add_mesh(
                self.generator.generatedObjects[i],
                show_edges=True,
                line_width=3,
                opacity=opacity,
                color=self.grayColor,
            )
        for i, pl in enumerate(self.plotters[3:]):
            pl.clear_actors()
            pl.add_mesh(
                self.generator.generatedObjects[i + 3],
                opacity=opacity,
                color=self.grayColor,
            )

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

    def update_progress(self, value):
        progress_labels = {
            1: "Generating tyvek tile",
            2: "Generating foam",
            3: "Generating magnet ring",
            4: "Generating base",
            5: "Generating bottom clip",
            6: "Generating top clip",
            7: "Generating mount",
            8: "Generation complete",
        }
        self.pbar.setValue(value / len(progress_labels) * 100)
        self.pbar.setFormat(progress_labels[value])

    def task_finished(self):
        self.regen_button.setEnabled(True)
        self.regen_button.setStyleSheet("background-color: #333333")
        for i, pl in enumerate(self.plotters[:3]):
            pl.clear_actors()
            pl.add_mesh(
                self.generator.generatedObjects[i],
                show_edges=True,
                line_width=3,
                color=self.interactorColor,
            )
        for i, pl in enumerate(self.plotters[3:]):
            pl.clear_actors()
            pl.add_mesh(
                self.generator.generatedObjects[i + 3], color=self.interactorColor
            )

        self.reset_view()

    def regen(self):
        messages = []
        if self.dataValidationCheckBox.isChecked():
            messages = self.generator.validate()
        if len(messages) == 0:
            self.regen_button.setEnabled(False)
            self.regen_button.setStyleSheet("background-color: #777777")
            self.threadpool.start(WorkerWrapper(self.generator))
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("\n\n".join(messages))
            msg.setWindowTitle("Validation Error")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            retval = msg.exec_()
