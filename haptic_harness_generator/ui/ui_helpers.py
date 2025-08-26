"""
UI helper functions and components
"""
from PyQt5 import QtWidgets, QtCore, QtGui
from typing import Dict, List, Optional
import json
from haptic_harness_generator.core.precision_handler import PrecisionHandler, format_display

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

        # Label with tooltip and word wrapping
        from haptic_harness_generator.core.config_manager import ConfigurationManager

        label = QtWidgets.QLabel(ConfigurationManager.get_parameter_display(self.param_def.name))
        label.setToolTip(f"{self.param_def.name}: {self.param_def.tooltip}")  # Enhanced tooltip
        label.setMinimumWidth(label_width)
        label.setMaximumWidth(label_width)
        label.setWordWrap(True)  # Enable word wrapping
        label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                padding: 5px;
                background-color: #2a2a2a;
                border-radius: 3px;
            }
            QLabel:hover {
                background-color: #3a3a3a;
                color: #ffffff;
            }
        """)

        # Input field
        self.input = QtWidgets.QLineEdit()
        # Format initial value with precision
        formatted_value = PrecisionHandler.round_value(self.param_def.default_value)
        self.input.setText(f"{formatted_value:.2f}")
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

        # Unit label with proper symbols
        unit_text = self.param_def.unit
        if unit_text == "degrees":
            unit_text = "°"
        elif unit_text == "mm":
            unit_text = "mm"
        elif not unit_text or unit_text == "":
            unit_text = "#"

        unit_label = QtWidgets.QLabel(unit_text)
        unit_label.setMinimumWidth(unit_width)
        unit_label.setMaximumWidth(unit_width)

        # Enhanced range label with improved styling
        range_text = f"{self.param_def.min_value:.0f}-{self.param_def.max_value:.0f}"
        range_label = QtWidgets.QLabel(range_text)
        range_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 2px 6px;
                border: 1px solid #3a3a4a;
                border-radius: 3px;
                background-color: #2a2a3a;
            }
            QLabel:hover {
                border-color: #4a4a5a;
                background-color: #3a3a4a;
            }
        """)
        range_label.setToolTip(f"Ideal range: {range_text} {unit_text}")
        range_label.setMinimumWidth(range_width)
        range_label.setMaximumWidth(range_width)

        # Add to grid with perfect alignment
        grid.addWidget(label, 0, 0)
        grid.addWidget(self.input, 0, 1)
        grid.addWidget(unit_label, 0, 2)
        grid.addWidget(range_label, 0, 3)

        self.setLayout(grid)

        # Connect signals with programmatic update check and precision handling
        self.input.textChanged.connect(self._on_text_changed)
        self.input.editingFinished.connect(self._on_editing_finished)

    def _on_text_changed(self, text):
        """Handle text changes, but only emit signal if not updating programmatically"""
        if not self._updating_programmatically:
            self.parameterChanged.emit(self.param_def.name, text)

    def _on_editing_finished(self):
        """Apply precision when user finishes editing"""
        if not self._updating_programmatically:
            try:
                value = float(self.input.text())
                rounded_value = PrecisionHandler.round_value(value)

                # Update display with proper formatting
                if rounded_value != value:
                    self._updating_programmatically = True
                    self.input.setText(f"{rounded_value:.2f}")
                    self._updating_programmatically = False
                    # Emit the rounded value
                    self.parameterChanged.emit(self.param_def.name, str(rounded_value))
            except ValueError:
                # Invalid input, let validation handle it
                pass
    
    def set_value(self, value):
        """Set parameter value programmatically without triggering change signal"""
        self._updating_programmatically = True
        # Apply precision to programmatically set values too
        rounded_value = PrecisionHandler.round_value(value)
        self.input.setText(f"{rounded_value:.2f}")
        self._updating_programmatically = False
    
    def get_value(self):
        """Get parameter value"""
        return self.input.text()
    
    def set_error(self, has_error):
        """Highlight field if it has an error with enhanced visual states"""
        if has_error:
            self.input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #ff4444;
                    background-color: #552222;
                    color: #ffaaaa;
                }
            """)
        else:
            # Normal state with hover effects
            self.input.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #3a3a4a;
                    background-color: #2a2a2a;
                    color: #ffffff;
                    padding: 3px;
                    border-radius: 3px;
                }
                QLineEdit:hover {
                    border-color: #4a4a5a;
                    background-color: #3a3a3a;
                }
                QLineEdit:focus {
                    border-color: #5a5a6a;
                    background-color: #3a3a3a;
                }
            """)

class ValidationDisplay(QtWidgets.QWidget):
    """Smart validation display that hides when valid"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Status indicator (always visible)
        self.status_label = QtWidgets.QLabel("Status: Not Validated")
        self.status_label.setStyleSheet("font-weight: bold; padding: 10px;")

        # Details section (collapsible)
        self.details_widget = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout()

        # Toggle button for collapsible details
        self.toggle_btn = QtWidgets.QPushButton("▼ Show Details")
        self.toggle_btn.setMaximumHeight(30)
        self.toggle_btn.clicked.connect(self.toggle_details)
        self.details_expanded = True

        # Error browser with increased height
        self.details_browser = QtWidgets.QTextBrowser()
        self.details_browser.setReadOnly(True)
        self.details_browser.setMaximumHeight(400)  # Increased from 250px
        self.details_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #2a2a2a;
                border: 1px solid #3a3a4a;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)

        details_layout.addWidget(self.toggle_btn)
        details_layout.addWidget(self.details_browser)
        self.details_widget.setLayout(details_layout)

        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(self.details_widget)

        self.setLayout(self.main_layout)

    def toggle_details(self):
        """Toggle the details section visibility"""
        self.details_expanded = not self.details_expanded
        self.details_browser.setVisible(self.details_expanded)
        self.toggle_btn.setText("▼ Show Details" if not self.details_expanded else "▲ Hide Details")
    
    def update_validation(self, result):
        """Update display with smart validation result"""
        if result.is_valid:
            self.set_valid_state()
        else:
            self.set_invalid_state(result)

    def set_valid_state(self):
        """Hide everything except success message"""
        self.details_widget.hide()
        self.setMaximumHeight(60)
        self.status_label.setText("✅ Configuration Valid - All parameters within acceptable ranges")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #44ff44;
                font-weight: bold;
                padding: 15px;
                background-color: #2a4a2a;
                border: 1px solid #44ff44;
                border-radius: 5px;
            }
        """)

    def set_invalid_state(self, result):
        """Show detailed error information"""
        self.details_widget.show()
        self.setMaximumHeight(500)  # Allow expansion

        # Update status with descriptive message
        error_count = len(result.errors)
        self.status_label.setText(f"Validation Status: {error_count} parameters need adjustment")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ff4444;
                font-weight: bold;
                padding: 10px;
                background-color: #4a2a2a;
                border: 1px solid #ff4444;
                border-radius: 5px;
            }
        """)

        # Format detailed content with highlighting
        content = self._format_validation_content(result)
        self.details_browser.setHtml(content)

        # Show details by default when invalid
        self.details_expanded = True
        self.details_browser.setVisible(True)
        self.toggle_btn.setText("▲ Hide Details")

    def _format_validation_content(self, result):
        """Format validation content with proper highlighting and precision"""
        html_content = []

        if result.errors:
            html_content.append('<h3 style="color: #ff6666;">❌ Errors:</h3>')
            for error in result.errors:
                # Highlight parameter references
                formatted_error = error.replace('[', '<b style="color: #ffaa66;">[').replace(']', ']</b>')
                html_content.append(f'<p style="color: #ffcccc; margin-left: 20px;">• {formatted_error}</p>')

        if result.suggestions:
            html_content.append('<h3 style="color: #66ff66;">💡 Suggestions:</h3>')
            for suggestion in result.suggestions:
                # Highlight actionable items and ensure precision formatting
                formatted_suggestion = suggestion.replace('→', '<b style="color: #66ff66;">→</b>')
                formatted_suggestion = formatted_suggestion.replace('Set ', '<b style="color: #aaffaa;">Set </b>')
                html_content.append(f'<p style="color: #ccffcc; margin-left: 20px;">• {formatted_suggestion}</p>')

        if result.warnings:
            html_content.append('<h3 style="color: #ffaa66;">⚠️ Warnings:</h3>')
            for warning in result.warnings:
                html_content.append(f'<p style="color: #ffffcc; margin-left: 20px;">• {warning}</p>')

        return ''.join(html_content)

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
    """Enhanced widget for selecting and managing presets with favorites"""

    presetChanged = QtCore.pyqtSignal(str)  # preset name

    def __init__(self, presets_dict, parent=None):
        super().__init__(parent)
        self.presets = presets_dict
        self.favorites = set()  # Track favorite presets
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Label (always visible in wide mode)
        self.label = QtWidgets.QLabel("Presets:")
        self.label.setMinimumWidth(60)
        self.label.setStyleSheet("color: #cccccc; font-weight: bold;")

        # Enhanced dropdown with styling
        self.combo = QtWidgets.QComboBox()
        self.combo.setMinimumWidth(200)
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
            QComboBox:hover {
                border-color: #5a5a5a;
                background-color: #4a4a4a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #cccccc;
            }
        """)

        self.populate_combo()
        self.combo.currentTextChanged.connect(self.on_preset_changed)

        layout.addWidget(self.label)
        layout.addWidget(self.combo)

        self.setLayout(layout)

    def populate_combo(self):
        """Populate combo box with favorites separated from regular presets"""
        self.combo.clear()
        self.combo.addItem("-- Custom --")

        # Add favorites first (if any)
        if self.favorites:
            self.combo.addItem("--- Favorites ---")
            for preset_name in sorted(self.favorites):
                if preset_name in self.presets:
                    self.combo.addItem(f"⭐ {preset_name}")

        # Add separator if we have both favorites and regular presets
        if self.favorites and len(self.presets) > len(self.favorites):
            self.combo.addItem("--- All Presets ---")

        # Add regular presets
        for preset_name in sorted(self.presets.keys()):
            if preset_name not in self.favorites:
                self.combo.addItem(preset_name)



    def on_preset_changed(self, preset_name):
        """Handle preset selection change"""
        # Clean up preset name (remove favorite star and separators)
        clean_name = preset_name.replace("⭐ ", "").strip()

        if clean_name not in ["-- Custom --", "--- Favorites ---", "--- All Presets ---"]:
            self.presetChanged.emit(clean_name)

    def set_custom(self):
        """Set to custom mode"""
        self.combo.setCurrentText("-- Custom --")

    def add_to_favorites(self, preset_name):
        """Add preset to favorites"""
        if preset_name in self.presets:
            self.favorites.add(preset_name)
            self.populate_combo()

    def remove_from_favorites(self, preset_name):
        """Remove preset from favorites"""
        self.favorites.discard(preset_name)
        self.populate_combo()

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
