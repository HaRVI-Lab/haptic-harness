from pyvistaqt import QtInteractor, MainWindow
from PyQt5 import QtCore, QtWidgets, Qt, QtGui, QtWebEngineWidgets
try:
    from .Styles import Styles
    from .Generator import Generator, WorkerWrapper
except ImportError:
    from Styles import Styles
    from Generator import Generator, WorkerWrapper
from time import perf_counter
import re
import os
from pyvista import Camera
import numpy as np

# Import new modular components
try:
    from .config_manager import ConfigurationManager
    from .validation_engine import ValidationEngine
    from .ui_helpers import (ParameterWidget, ValidationDisplay, ScalingHelper,
                            PresetSelector, ConfigurationButtons, ParameterCategory)
except ImportError:
    from config_manager import ConfigurationManager
    from validation_engine import ValidationEngine
    from ui_helpers import (ParameterWidget, ValidationDisplay, ScalingHelper,
                           PresetSelector, ConfigurationButtons, ParameterCategory)

current_dir = os.path.dirname(os.path.abspath(__file__))
rotate_icon_path = os.path.join(current_dir, "rotateIcon.png")
anatomy_of_tile_path = os.path.join(current_dir, "hapticsNew.jpg")

# Use ConfigurationManager for presets instead of hardcoded values
PRESET_CONFIGS = ConfigurationManager.PRESETS


class MyMainWindow(MainWindow):

    def __init__(self, userDir, parent=None, show=True):
        QtWidgets.QMainWindow.__init__(self, parent)

        # Initialize modular components
        self.userDir = userDir
        self.generator = Generator(userDir)
        self.validator = ValidationEngine()
        self.parameter_widgets = {}
        self.parameter_categories = {}

        # Connect generator signals
        self.generator.signals.progress.connect(self.update_progress)
        self.generator.signals.finished.connect(self.task_finished)
        self.threadpool = QtCore.QThreadPool()

        # Apply styling
        styleSheet = Styles()
        super().setStyleSheet(styleSheet.getStyles())
        self.interactorColor = styleSheet.colors["green"]
        self.grayColor = styleSheet.colors["lightGray"]

        # Apply DPI-scaled styles
        self.apply_scaled_styles()

        # Create main layout
        primaryLayout = Qt.QHBoxLayout()
        self.frame = QtWidgets.QFrame()
        self.plotters = []

        # Progress bar
        self.pbar = QtWidgets.QProgressBar(self)
        self.pbar.setFormat("Initialized")
        self.pbar.setValue(100)

        # Data validation checkbox (keep for compatibility)
        self.dataValidationCheckBox = QtWidgets.QCheckBox("Data Validation", self)
        self.dataValidationCheckBox.setChecked(True)
        self.dataValidationCheckBox.clicked.connect(self.setDataValidation)

        # Create main panels
        self.parameter_panel = self.create_parameter_panel()
        primaryLayout.addWidget(self.parameter_panel)
        primaryLayout.addWidget(self.createDiagram())
        primaryLayout.addWidget(self.objectsPane(), stretch=4)

        centralWidget = Qt.QWidget(objectName="totalBackground")
        centralWidget.setLayout(primaryLayout)
        self.setCentralWidget(centralWidget)

        if show:
            self.show()

    def apply_scaled_styles(self):
        """Apply DPI-scaled styles"""
        scale = ScalingHelper.get_scale_factor()
        base_font = ScalingHelper.scale_font(14)

        # Additional styling for modular components
        style = f"""
            QWidget {{
                font-size: {base_font}px;
            }}
            QPushButton {{
                padding: {int(5*scale)}px;
                border-radius: {int(3*scale)}px;
            }}
            QLineEdit {{
                padding: {int(3*scale)}px;
            }}
        """
        # Apply additional styles without overriding existing ones
        current_style = self.styleSheet()
        self.setStyleSheet(current_style + style)

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

    def createDiagram(self):
        scroll_area = QtWidgets.QScrollArea()

        label = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap(anatomy_of_tile_path)
        pixmap.setDevicePixelRatio(2.0)

        # Use parameter panel width for scaling, with fallback to reasonable default
        try:
            panel_width = self.parameter_panel.width() if hasattr(self, 'parameter_panel') else 400
            # If width is 0 (not yet rendered), use a reasonable default
            target_width = panel_width * 1.5 if panel_width > 0 else 600
        except (AttributeError, TypeError):
            target_width = 600  # Fallback default

        scaled_pixmap = pixmap.scaledToWidth(
            int(target_width), mode=QtCore.Qt.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)

        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(label)
        return scroll_area

    def create_parameter_panel(self):
        """Create parameter input panel using modular components"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 30, 20)

        # Preset selector
        self.preset_selector = PresetSelector(ConfigurationManager.PRESETS)
        self.preset_selector.presetChanged.connect(self.load_preset)
        layout.addWidget(self.preset_selector)

        # Add separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(separator)

        # Create parameter categories using ConfigurationManager
        scroll = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout()

        # Group parameters by category
        categories = {}
        for param_name, param_def in ConfigurationManager.PARAMETERS.items():
            if param_def.category not in categories:
                categories[param_def.category] = []
            categories[param_def.category].append((param_name, param_def))

        # Create parameter widgets by category
        for category_name, params in categories.items():
            category_widget = ParameterCategory(category_name, params)
            self.parameter_categories[category_name] = category_widget

            # Connect parameter change signals
            for param_name, widget in category_widget.get_parameter_widgets().items():
                widget.parameterChanged.connect(self.on_parameter_changed)
                self.parameter_widgets[param_name] = widget

            scroll_layout.addWidget(category_widget)

            # Add separator between categories
            separator = QtWidgets.QFrame()
            separator.setFrameShape(QtWidgets.QFrame.HLine)
            separator.setFrameShadow(QtWidgets.QFrame.Sunken)
            scroll_layout.addWidget(separator)


        # Validation display
        self.validation_display = ValidationDisplay()
        scroll_layout.addWidget(self.validation_display)

        # Configuration buttons
        self.config_buttons = ConfigurationButtons()
        self.config_buttons.validateRequested.connect(self.validate_configuration)
        self.config_buttons.generateRequested.connect(self.generate_parts)
        self.config_buttons.exportRequested.connect(self.export_configuration)
        self.config_buttons.importRequested.connect(self.import_configuration)
        scroll_layout.addWidget(self.config_buttons)

        # Data validation checkbox (keep for compatibility)
        scroll_layout.addWidget(self.dataValidationCheckBox)

        # Info labels
        info_label = QtWidgets.QLabel(
            '<p style="color: #999999; font-size: 16px; font-style: italic;">2D file type is .dxf; 3D file type is .stl</p>'
        )
        info_label.setAlignment(QtCore.Qt.AlignCenter)
        scroll_layout.addWidget(info_label)

        github_label = QtWidgets.QLabel(
            '<a href="https://github.com/HaRVI-Lab/haptic-harness" style="color: #339955; font-size: 16px;">Instructions on GitHub</a>'
        )
        github_label.setAlignment(QtCore.Qt.AlignCenter)
        github_label.setOpenExternalLinks(True)
        scroll_layout.addWidget(github_label)

        # Setup scroll area
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        layout.addWidget(scroll)
        panel.setLayout(layout)

        return panel

    def on_parameter_changed(self, param_name, value):
        """Handle parameter value changes"""
        self.setGeneratorAttribute(param_name, value)
        self.preset_selector.set_custom()  # Switch to custom mode

    def load_preset(self, preset_name):
        """Load a preset configuration"""
        if preset_name in ConfigurationManager.PRESETS:
            config = ConfigurationManager.PRESETS[preset_name]

            # Update all parameter widgets
            for category_widget in self.parameter_categories.values():
                category_widget.set_values(config)

            # Apply to generator
            for param_name, value in config.items():
                if hasattr(self.generator, param_name):
                    # Handle angle conversions
                    if param_name in ["mountBottomAngleOpening", "mountTopAngleOpening"]:
                        value = value * np.pi / 180  # Convert to radians
                    setattr(self.generator, param_name, value)

            # Update display
            self.grayOutPlotters()
            self.pbar.setValue(0)
            self.pbar.setFormat("Preset Loaded - Ready to Generate")

            # Auto-validate
            self.validate_configuration()

    def validate_configuration(self):
        """Validate current configuration"""
        # Gather current values from all categories
        config = {}
        for category_widget in self.parameter_categories.values():
            config.update(category_widget.get_values())

        # Validate using the validation engine
        result = self.validator.validate_complete(config)

        # Update validation display
        self.validation_display.update_validation(result)

        # Highlight error fields
        for param_name, widget in self.parameter_widgets.items():
            widget.set_error(param_name in result.affected_parameters)

        # Enable/disable generate button
        self.config_buttons.set_generate_enabled(result.is_valid)

        return result.is_valid

    def generate_parts(self):
        """Generate parts if configuration is valid"""
        if not self.validate_configuration():
            QtWidgets.QMessageBox.warning(
                self,
                "Validation Failed",
                "Please fix validation errors before generating."
            )
            return

        # Use the existing regen method
        self.regen()

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
        for i in range(5):
            self.plotters[i + 3].camera = self.settings[i].copy()

    def initPeripheralsPane(self):

        plotLayout = Qt.QVBoxLayout()
        subPlotLayout = Qt.QHBoxLayout()

        labels = ["Base", "Bottom Clip", "Top Clip", "Mount", "Strap Clip"]

        for i in range(2):
            subPlotLayout = Qt.QHBoxLayout()
            for j in range(3):
                if (i * 3 + j) == 5:
                    continue
                section = QtWidgets.QVBoxLayout()
                interactor = QtInteractor(self.frame)
                self.plotters.append(interactor)
                label = QtWidgets.QLabel(labels[i * 3 + j], objectName="sectionHeader")
                label.setAlignment(QtCore.Qt.AlignCenter)
                section.addWidget(label)
                section.addWidget(self.plotters[-1].interactor)
                frame = Qt.QFrame(objectName="sectionFrame")
                frame.setFrameShape(Qt.QFrame.StyledPanel)
                frame.setLayout(section)
                subPlotLayout.addWidget(frame)
                self.plotters[-1].add_mesh(
                    self.generator.generatedObjects[i * 3 + j + 3],
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
            8: "Generating strap clip",
            9: "Generation complete",
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



    def export_configuration(self):
        """Export current configuration using ConfigurationManager"""
        from PyQt5.QtWidgets import QFileDialog

        # Gather current configuration from parameter widgets
        config = {}
        for category_widget in self.parameter_categories.values():
            config.update(category_widget.get_values())

        # Handle angle conversions for export (convert radians to degrees)
        for param_name in ["mountBottomAngleOpening", "mountTopAngleOpening"]:
            if param_name in config:
                # Get the actual value from generator (which is in radians)
                generator_value = getattr(self.generator, param_name, 0)
                config[param_name] = generator_value * 180 / np.pi

        # Get filename from user
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Configuration",
            f"{self.userDir}/config.json",
            "JSON Files (*.json)"
        )

        if filename:
            success = ConfigurationManager.export_config(config, filename)

            if success:
                QtWidgets.QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Configuration exported to {filename}"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Export Failed",
                    "Failed to export configuration. Check file permissions."
                )

    def import_configuration(self):
        """Import configuration using ConfigurationManager"""
        from PyQt5.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Configuration",
            self.userDir,
            "JSON Files (*.json)"
        )

        if filename:
            config = ConfigurationManager.import_config(filename)

            if config is not None:
                # Update parameter widgets
                for category_widget in self.parameter_categories.values():
                    category_widget.set_values(config)

                # Apply to generator
                for param_name, value in config.items():
                    if hasattr(self.generator, param_name):
                        # Handle angle conversions
                        if param_name in ["mountBottomAngleOpening", "mountTopAngleOpening"]:
                            value = value * np.pi / 180  # Convert to radians
                        setattr(self.generator, param_name, value)

                # Update UI
                self.grayOutPlotters()
                self.pbar.setValue(0)
                self.pbar.setFormat("Configuration Imported - Ready to Generate")

                # Switch to custom mode and validate
                self.preset_selector.set_custom()
                self.validate_configuration()

                QtWidgets.QMessageBox.information(
                    self,
                    "Import Successful",
                    "Configuration imported successfully"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Import Failed",
                    "Failed to import configuration. Check file format and try again."
                )
