"""
UI helper functions and components
"""
from PyQt5 import QtWidgets, QtCore, QtGui
from typing import Dict, List, Optional
import json

class ParameterWidget(QtWidgets.QWidget):
    """Custom widget for parameter input with validation"""

    parameterChanged = QtCore.pyqtSignal(str, str)  # name, value

    def __init__(self, param_def, parent=None):
        super().__init__(parent)
        self.param_def = param_def
        self._updating_programmatically = False
        self.setup_ui()
    
    def setup_ui(self):
        # Use QGridLayout for perfect alignment
        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(4, 1)  # Last column stretches

        # Fixed column widths for consistent alignment
        label_width = 300
        input_width = 80
        unit_width = 40
        range_width = 100

        # Label with tooltip using improved display method
        from haptic_harness_generator.core.config_manager import ConfigurationManager

        label = QtWidgets.QLabel(ConfigurationManager.get_parameter_display(self.param_def.name))
        label.setToolTip(self.param_def.tooltip)
        label.setMinimumWidth(label_width)
        label.setMaximumWidth(label_width)

        # Input field
        self.input = QtWidgets.QLineEdit()
        self.input.setText(str(self.param_def.default_value))
        self.input.setMinimumWidth(input_width)
        self.input.setMaximumWidth(input_width)
        self.input.setAlignment(QtCore.Qt.AlignRight)

        # Validator
        if self.param_def.unit and self.param_def.unit != "":
            validator = QtGui.QDoubleValidator(
                self.param_def.min_value,
                self.param_def.max_value,
                2
            )
        else:
            validator = QtGui.QIntValidator(
                int(self.param_def.min_value),
                int(self.param_def.max_value)
            )
        self.input.setValidator(validator)

        # Unit label
        unit_label = QtWidgets.QLabel(self.param_def.unit)
        unit_label.setMinimumWidth(unit_width)
        unit_label.setMaximumWidth(unit_width)

        # Enhanced range label with color coding
        range_text = f"{self.param_def.min_value}-{self.param_def.max_value}"
        range_label = QtWidgets.QLabel(range_text)
        range_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 2px 6px;
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #2a2a2a;
            }
        """)
        range_label.setToolTip(f"Valid range: {range_text} {self.param_def.unit}")
        range_label.setMinimumWidth(range_width)
        range_label.setMaximumWidth(range_width)

        # Add to grid with perfect alignment
        grid.addWidget(label, 0, 0)
        grid.addWidget(self.input, 0, 1)
        grid.addWidget(unit_label, 0, 2)
        grid.addWidget(range_label, 0, 3)

        self.setLayout(grid)

        # Connect signal with programmatic update check
        self.input.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text):
        """Handle text changes, but only emit signal if not updating programmatically"""
        if not self._updating_programmatically:
            self.parameterChanged.emit(self.param_def.name, text)
    
    def set_value(self, value):
        """Set parameter value programmatically without triggering change signal"""
        self._updating_programmatically = True
        self.input.setText(str(value))
        self._updating_programmatically = False
    
    def get_value(self):
        """Get parameter value"""
        return self.input.text()
    
    def set_error(self, has_error):
        """Highlight field if it has an error"""
        if has_error:
            self.input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #ff4444;
                    background-color: #552222;
                }
            """)
        else:
            self.input.setStyleSheet("")

class ValidationDisplay(QtWidgets.QWidget):
    """Widget to display validation results"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        # Status indicator
        self.status_label = QtWidgets.QLabel("Status: Not Validated")
        self.status_label.setStyleSheet("font-weight: bold;")
        
        # Error list
        self.error_list = QtWidgets.QTextEdit()
        self.error_list.setReadOnly(True)
        self.error_list.setMaximumHeight(150)
        
        # Suggestion box
        self.suggestion_box = QtWidgets.QTextEdit()
        self.suggestion_box.setReadOnly(True)
        self.suggestion_box.setMaximumHeight(100)
        self.suggestion_box.setStyleSheet("background-color: #2a2a3a;")
        
        layout.addWidget(self.status_label)
        layout.addWidget(QtWidgets.QLabel("Errors:"))
        layout.addWidget(self.error_list)
        layout.addWidget(QtWidgets.QLabel("Suggestions:"))
        layout.addWidget(self.suggestion_box)
        
        self.setLayout(layout)
    
    def update_validation(self, result):
        """Update display with validation result"""
        if result.is_valid:
            self.status_label.setText("Status: ✓ Valid")
            self.status_label.setStyleSheet("color: #44ff44; font-weight: bold;")
            self.error_list.clear()
            self.suggestion_box.clear()
        else:
            self.status_label.setText(f"Status: ✗ {len(result.errors)} Errors")
            self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
            
            # Display errors
            self.error_list.setPlainText("\n".join(result.errors))
            
            # Display suggestions
            if result.suggestions:
                self.suggestion_box.setPlainText("\n".join(result.suggestions))
            else:
                self.suggestion_box.clear()
        
        # Display warnings if any
        if result.warnings:
            warning_text = "WARNINGS:\n" + "\n".join(result.warnings)
            if result.is_valid:
                self.error_list.setPlainText(warning_text)
            else:
                current_text = self.error_list.toPlainText()
                self.error_list.setPlainText(current_text + "\n\n" + warning_text)

class ScalingHelper:
    """Helper for DPI scaling"""
    
    @staticmethod
    def get_scale_factor():
        """Get DPI scale factor"""
        app = QtWidgets.QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                dpi = screen.logicalDotsPerInch()
                return dpi / 96.0
        return 1.0
    
    @staticmethod
    def scale_font(base_size):
        """Scale font size for DPI"""
        return int(base_size * ScalingHelper.get_scale_factor())
    
    @staticmethod
    def scale_size(base_size):
        """Scale any size value for DPI"""
        return int(base_size * ScalingHelper.get_scale_factor())

class PresetSelector(QtWidgets.QWidget):
    """Widget for selecting and managing presets"""
    
    presetChanged = QtCore.pyqtSignal(str)  # preset name
    
    def __init__(self, presets_dict, parent=None):
        super().__init__(parent)
        self.presets = presets_dict
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout()
        
        # Label
        label = QtWidgets.QLabel("Preset:")
        label.setMinimumWidth(60)
        
        # Dropdown
        self.combo = QtWidgets.QComboBox()
        self.combo.addItem("-- Custom --")
        for preset_name in self.presets.keys():
            self.combo.addItem(preset_name)
        
        self.combo.currentTextChanged.connect(self.on_preset_changed)
        
        layout.addWidget(label)
        layout.addWidget(self.combo)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def on_preset_changed(self, preset_name):
        """Handle preset selection change"""
        if preset_name != "-- Custom --":
            self.presetChanged.emit(preset_name)
    
    def set_custom(self):
        """Set to custom mode"""
        self.combo.setCurrentText("-- Custom --")

class ConfigurationButtons(QtWidgets.QWidget):
    """Widget for configuration management buttons"""
    
    exportRequested = QtCore.pyqtSignal()
    importRequested = QtCore.pyqtSignal()
    validateRequested = QtCore.pyqtSignal()
    generateRequested = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        # Validation and generation buttons
        action_layout = QtWidgets.QHBoxLayout()
        
        self.validate_btn = QtWidgets.QPushButton("Validate")
        self.validate_btn.clicked.connect(self.validateRequested.emit)
        
        self.generate_btn = QtWidgets.QPushButton("Generate")
        self.generate_btn.clicked.connect(self.generateRequested.emit)
        
        action_layout.addWidget(self.validate_btn)
        action_layout.addWidget(self.generate_btn)
        
        # Export/Import buttons
        io_layout = QtWidgets.QHBoxLayout()
        
        self.export_btn = QtWidgets.QPushButton("Export Config")
        self.export_btn.clicked.connect(self.exportRequested.emit)
        
        self.import_btn = QtWidgets.QPushButton("Import Config")
        self.import_btn.clicked.connect(self.importRequested.emit)
        
        io_layout.addWidget(self.export_btn)
        io_layout.addWidget(self.import_btn)
        
        layout.addLayout(action_layout)
        layout.addLayout(io_layout)
        
        self.setLayout(layout)
    
    def set_generate_enabled(self, enabled):
        """Enable/disable generate button"""
        self.generate_btn.setEnabled(enabled)
        if enabled:
            self.generate_btn.setStyleSheet("")
        else:
            self.generate_btn.setStyleSheet("background-color: #777777")

class ParameterCategory(QtWidgets.QWidget):
    """Widget for grouping parameters by category"""
    
    def __init__(self, category_name, parameters, parent=None):
        super().__init__(parent)
        self.category_name = category_name
        self.parameters = parameters
        self.parameter_widgets = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        # Category header
        header = QtWidgets.QLabel(self.category_name)
        header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #999999;
                padding: 5px 0px;
                border-bottom: 1px solid #444444;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header)
        
        # Parameter widgets
        for param_name, param_def in self.parameters:
            widget = ParameterWidget(param_def)
            self.parameter_widgets[param_name] = widget
            layout.addWidget(widget)
        
        self.setLayout(layout)
    
    def get_parameter_widgets(self):
        """Get all parameter widgets in this category"""
        return self.parameter_widgets
    
    def set_values(self, values_dict):
        """Set values for parameters in this category"""
        for param_name, value in values_dict.items():
            if param_name in self.parameter_widgets:
                self.parameter_widgets[param_name].set_value(value)
    
    def get_values(self):
        """Get all parameter values from this category"""
        values = {}
        for param_name, widget in self.parameter_widgets.items():
            value_str = widget.get_value()
            if value_str:
                try:
                    # Try to convert to appropriate type
                    if '.' in value_str:
                        values[param_name] = float(value_str)
                    else:
                        values[param_name] = int(value_str)
                except ValueError:
                    pass  # Skip invalid values
        return values
