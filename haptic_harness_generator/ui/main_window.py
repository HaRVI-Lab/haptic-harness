from pyvistaqt import QtInteractor, MainWindow
from PyQt5 import QtCore, QtWidgets, Qt, QtGui
from haptic_harness_generator.ui.styles import Styles
from haptic_harness_generator.core.generator import Generator, WorkerWrapper
from time import perf_counter
import re
import os
from pyvista import Camera
import numpy as np

# Import new modular components
from haptic_harness_generator.core.config_manager import ConfigurationManager
from haptic_harness_generator.core.validation_engine import ValidationEngine
from haptic_harness_generator.ui.ui_helpers import (ParameterWidget, ValidationDisplay, ScalingHelper,
                        PresetSelector, ParameterCategory)

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rotate_icon_path = os.path.join(current_dir, "assets", "rotateIcon.png")
anatomy_of_tile_path = os.path.join(current_dir, "assets", "hapticsNew.jpg")

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

        # Setup validation timer for debounced auto-validation
        self.validation_timer = QtCore.QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.validate_configuration)

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
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        # Title section
        title = QtWidgets.QLabel("Reference Diagram")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
                background-color: #2a2a3a;
                border-radius: 5px;
            }
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)

        subtitle = QtWidgets.QLabel("← Numbered areas correspond to parameters")
        subtitle.setStyleSheet("color: #888888; font-style: italic;")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)

        # Existing scroll area with image
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

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(scroll_area)
        container.setLayout(layout)

        return container

    def create_parameter_panel(self):
        """Create parameter input panel with fixed validation section"""
        panel = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 30, 20)

        # Top section - Streamlined preset bar with compact buttons
        top_section = QtWidgets.QWidget()
        top_section.setMaximumHeight(50)  # Reduced from 80px to 50px
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 5)  # Reduced bottom margin

        # Preset selector (left side)
        self.preset_selector = PresetSelector(ConfigurationManager.PRESETS)
        self.preset_selector.presetChanged.connect(self.load_preset)
        top_layout.addWidget(self.preset_selector)

        # Spacer to push buttons to the right
        top_layout.addStretch()

        # Export/Import buttons (right side) - Compact design
        self.export_btn = QtWidgets.QPushButton("Export")
        self.export_btn.clicked.connect(self.export_configuration)
        self.export_btn.setMaximumWidth(70)  # Reduced from 80px
        self.export_btn.setMaximumHeight(30)  # Compact height
        self.export_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 3px;
            }
        """)

        self.import_btn = QtWidgets.QPushButton("Import")
        self.import_btn.clicked.connect(self.import_configuration)
        self.import_btn.setMaximumWidth(70)  # Reduced from 80px
        self.import_btn.setMaximumHeight(30)  # Compact height
        self.import_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 3px;
            }
        """)

        top_layout.addWidget(self.export_btn)
        top_layout.addWidget(self.import_btn)
        top_section.setLayout(top_layout)

        # Pinned messages section - Enhanced with range clarification
        messages_section = QtWidgets.QWidget()
        messages_section.setMaximumHeight(70)  # Reduced from 80px
        messages_layout = QtWidgets.QVBoxLayout()
        messages_layout.setContentsMargins(0, 0, 0, 5)  # Reduced bottom margin

        # First message - parameter numbers
        ref_note = QtWidgets.QLabel(
            "📌 Numbers [1-25] in parameters correspond to labeled areas in the reference diagram →"
        )
        ref_note.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-style: italic;
                font-size: 12px;
                padding: 3px 5px;
                background-color: #2a2a3a;
                border-radius: 3px;
                margin-bottom: 1px;
            }
        """)

        # Second message - range clarification
        range_note = QtWidgets.QLabel(
            "📌 Ranges shown (e.g., 20-50 for [1]) indicate ideal values for that parameter"
        )
        range_note.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-style: italic;
                font-size: 12px;
                padding: 3px 5px;
                background-color: #2a2a3a;
                border-radius: 3px;
            }
        """)

        messages_layout.addWidget(ref_note)
        messages_layout.addWidget(range_note)
        messages_layout.setSpacing(2)  # Minimal spacing between messages
        messages_section.setLayout(messages_layout)

        # Middle section - Scrollable parameters
        scroll = QtWidgets.QScrollArea()
        scroll.setMinimumHeight(300)
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

        # Setup scroll area for parameters only
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Bottom section - Expanded validation panel
        bottom_section = QtWidgets.QWidget()
        bottom_section.setMinimumHeight(300)
        bottom_section.setMaximumHeight(450)  # Increased from 400px
        bottom_layout = QtWidgets.QVBoxLayout()

        # Validation display with expanded height
        self.validation_display = ValidationDisplay()
        self.validation_display.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )

        # Action buttons (Validate and Generate only)
        action_layout = QtWidgets.QHBoxLayout()

        # Smaller validate button since validation runs automatically
        self.validate_btn = QtWidgets.QPushButton("Validate")
        self.validate_btn.clicked.connect(self.validate_configuration)
        self.validate_btn.setMaximumWidth(80)  # Compact width
        self.validate_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 6px 10px;
                color: #aaaaaa;
                border-radius: 3px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)

        self.generate_btn = QtWidgets.QPushButton("Generate")
        self.generate_btn.clicked.connect(self.generate_parts)

        action_layout.addWidget(self.validate_btn)
        action_layout.addWidget(self.generate_btn)
        action_layout.addStretch()

        # Data validation checkbox (keep for compatibility)
        action_layout.addWidget(self.dataValidationCheckBox)

        # Consolidated info line at bottom
        info_layout = QtWidgets.QHBoxLayout()
        info_layout.setContentsMargins(0, 10, 0, 0)

        info_label = QtWidgets.QLabel(
            '<span style="color: #999999; font-size: 14px; font-style: italic;">2D file type is .dxf; 3D file type is .stl</span>'
        )

        github_label = QtWidgets.QLabel(
            '<a href="https://github.com/HaRVI-Lab/haptic-harness" style="color: #339955; font-size: 14px;">Instructions on GitHub</a>'
        )
        github_label.setOpenExternalLinks(True)

        info_layout.addWidget(info_label)
        info_layout.addStretch()  # Spacer between info and GitHub link
        info_layout.addWidget(github_label)

        bottom_layout.addWidget(self.validation_display)
        bottom_layout.addLayout(action_layout)
        bottom_layout.addLayout(info_layout)
        bottom_section.setLayout(bottom_layout)

        # Add all sections to main layout
        main_layout.addWidget(top_section)
        main_layout.addWidget(messages_section)
        main_layout.addWidget(scroll, stretch=1)  # Scroll gets stretch
        main_layout.addWidget(bottom_section)

        panel.setLayout(main_layout)
        return panel

    def on_parameter_changed(self, param_name, value):
        """Handle parameter value changes with robust error handling"""
        try:
            self.setGeneratorAttribute(param_name, value)
            # Only switch to custom if this is a user edit, not programmatic update
            if not self.parameter_widgets[param_name]._updating_programmatically:
                self.preset_selector.set_custom()  # Switch to custom mode
                # Debounced validation - wait 500ms after last change
                self.validation_timer.stop()
                self.validation_timer.start(500)
        except Exception as e:
            # Log the error but don't crash the application
            print(f"Warning: Failed to update parameter {param_name} with value '{value}': {e}")
            # The parameter widget will handle visual feedback
            pass

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
                    # Ensure integer parameters are actually integers
                    elif param_name in ["numSides", "numMagnetsInRing"]:
                        value = int(value)
                    setattr(self.generator, param_name, value)

            # Update display
            self.grayOutPlotters()
            self.pbar.setValue(0)
            self.pbar.setFormat("Preset Loaded - Ready to Generate")

            # Auto-validate
            self.validate_configuration()

    def validate_configuration(self):
        """Validate current configuration with enhanced visual feedback"""
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

        # Enable/disable generate button with visual feedback
        self.generate_btn.setEnabled(result.is_valid)

        # Add visual feedback to generate button
        if result.is_valid:
            self.generate_btn.setStyleSheet("""
                QPushButton {
                    background-color: #44aa44;
                    border: 2px solid #66ff66;
                    font-weight: bold;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #55bb55;
                }
            """)
            self.pbar.setFormat("✓ Valid Configuration - Ready to Generate")
        else:
            self.generate_btn.setStyleSheet("")
            self.pbar.setFormat(f"✗ {len(result.errors)} errors to fix")

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

        # Auto-save configuration before generation
        try:
            current_config = self.get_current_configuration()
            success = ConfigurationManager.auto_save_config(current_config, self.userDir)

            if success:
                # Update progress bar to show auto-save success
                self.pbar.setFormat("Configuration auto-saved - Starting generation...")
            else:
                # Show warning but don't stop generation
                QtWidgets.QMessageBox.warning(
                    self,
                    "Auto-save Warning",
                    "Failed to auto-save configuration, but generation will continue."
                )
        except Exception as e:
            # Log error but don't stop generation
            print(f"Auto-save error: {e}")
            QtWidgets.QMessageBox.warning(
                self,
                "Auto-save Warning",
                f"Failed to auto-save configuration: {str(e)}\nGeneration will continue."
            )

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

        labels = ["Base", "Bottom Clip", "Magnet Clip", "Mount", "Strap Clip"]

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
                # Add rotation hint text instead of logo (PyVista 0.42.3 compatible)
                self.plotters[-1].add_text(
                    "↻ Drag to rotate",
                    position='lower_left',
                    font_size=8,
                    color='gray'
                )
            plotLayout.addLayout(subPlotLayout)

        frame = Qt.QFrame(objectName="sectionFrame")
        frame.setFrameShape(Qt.QFrame.StyledPanel)
        frame.setLayout(plotLayout)

        return frame

    def setGeneratorAttribute(self, attrName, val):
        """Set generator attribute with error handling for invalid inputs"""
        try:
            self.generator.customSetAttr(attrName=attrName, val=val)
            self.grayOutPlotters()
            self.pbar.setValue(0)
            self.pbar.setFormat("Ready to Generate")
        except Exception as e:
            # Log the error but don't crash the application
            print(f"Warning: Failed to set generator attribute {attrName} to '{val}': {e}")
            # Keep the UI in a consistent state
            self.pbar.setFormat("Parameter Error - Check Input")
            # Don't update the plotters if there was an error
            pass

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
            6: "Generating magnet clip",
            7: "Generating mount",
            8: "Generating strap clip",
            9: "Generation complete",
        }
        self.pbar.setValue(value / len(progress_labels) * 100)
        self.pbar.setFormat(progress_labels[value])

    def task_finished(self):
        self.generate_btn.setEnabled(True)
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
            self.generate_btn.setEnabled(False)
            self.threadpool.start(WorkerWrapper(self.generator))
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("\n\n".join(messages))
            msg.setWindowTitle("Validation Error")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            retval = msg.exec_()



    def get_current_configuration(self):
        """
        Collect current configuration state from all parameter widgets.

        Returns:
            dict: Current configuration with proper type conversions and angle handling
        """
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

        return config

    def export_configuration(self):
        """Export current configuration using ConfigurationManager"""
        from PyQt5.QtWidgets import QFileDialog

        # Use the helper method to get current configuration
        config = self.get_current_configuration()

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
                        # Ensure integer parameters are always integers
                        elif param_name in ["numSides", "numMagnetsInRing"]:
                            value = int(value)
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
