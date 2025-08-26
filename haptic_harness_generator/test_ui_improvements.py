"""
Comprehensive test suite for UI improvements
Tests all implemented fixes and features from the haptic-ui-implementation guide
"""
import pytest
import sys
import os
import tempfile
from unittest.mock import Mock, patch
from PyQt5 import QtWidgets, QtCore, QtTest
from PyQt5.QtTest import QTest

# Add the package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only the components we can test without full dependencies
from config_manager import ConfigurationManager
from validation_engine import ValidationEngine
from ui_helpers import ParameterWidget, PresetSelector, ValidationDisplay


class TestParameterWidgetBehavior:
    """Test Fix 1: Parameter Widget Programmatic Update Flag"""

    def setup_method(self):
        """Setup test environment"""
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])

    def test_programmatic_update_flag(self):
        """Test that programmatic updates don't trigger change signals"""
        param_def = ConfigurationManager.PARAMETERS['concentricPolygonRadius']
        widget = ParameterWidget(param_def)

        # Track signal emissions
        signal_emitted = []
        widget.parameterChanged.connect(lambda name, value: signal_emitted.append((name, value)))

        # Programmatic update should not emit signal
        widget.set_value("25")
        assert len(signal_emitted) == 0

        # Manual text change should emit signal
        widget.input.setText("30")
        widget.input.textChanged.emit("30")
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == ('concentricPolygonRadius', '30')


class TestParameterLabelImprovements:
    """Test Fix 3: Parameter Label Improvements"""
    
    def setup_method(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])
    
    def test_parameter_display_formatting(self):
        """Test improved parameter display formatting"""
        # Test parameter with ui_number > 0
        display = ConfigurationManager.get_parameter_display('concentricPolygonRadius')
        assert display == "[1] Concentric Polygon Radius"
        
        # Test parameter with ui_number = 0 (should not show [0])
        display = ConfigurationManager.get_parameter_display('numSides')
        assert display == "Number of Sides"  # No [0] bracket
    
    def test_range_label_styling(self):
        """Test enhanced range label styling"""
        param_def = ConfigurationManager.PARAMETERS['concentricPolygonRadius']
        widget = ParameterWidget(param_def)
        
        # Check that range label has enhanced styling
        range_labels = widget.findChildren(QtWidgets.QLabel)
        range_label = None
        for label in range_labels:
            if "20-50" in label.text():  # Range for concentricPolygonRadius
                range_label = label
                break
        
        assert range_label is not None
        style = range_label.styleSheet()
        assert "border-radius" in style
        assert "background-color" in style


class TestValidationImprovements:
    """Test validation engine improvements"""
    
    def setup_method(self):
        self.validator = ValidationEngine()
    
    def test_comprehensive_suggestions(self):
        """Test that suggestions are provided for all error types"""
        # Create a config with multiple errors
        config = {
            'concentricPolygonRadius': 30,
            'slotWidth': 35,  # Too wide for polygon
            'tactorRadius': 15,  # Too large for magnet ring
            'magnetRingRadius': 20,
            'numSides': 6
        }
        
        result = self.validator.validate_complete(config)
        
        # Should have errors
        assert not result.is_valid
        assert len(result.errors) > 0
        
        # Should have suggestions for each error
        assert len(result.suggestions) > 0
        
        # Suggestions should be specific
        for suggestion in result.suggestions:
            assert len(suggestion) > 20  # Not just generic text
    
    def test_tolerance_in_suggestions(self):
        """Test that suggested values include safety margins"""
        config = {
            'concentricPolygonRadius': 30,
            'slotWidth': 35,  # Too wide
            'numSides': 6
        }
        
        result = self.validator.validate_complete(config)
        
        # Extract suggested values from suggestions
        for suggestion in result.suggestions:
            if "Set" in suggestion and "slotWidth" in suggestion:
                # Should suggest a value with safety margin
                import re
                value_match = re.search(r'to (\d+)', suggestion)
                if value_match:
                    suggested_value = int(value_match.group(1))
                    # Should be less than theoretical maximum to include safety margin
                    theoretical_max = 2 * 30 * 0.577  # tan(pi/6) ≈ 0.577
                    assert suggested_value < theoretical_max


class TestPresetSelector:
    """Test preset selector functionality"""

    def setup_method(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])

    def test_preset_selector_creation(self):
        """Test that preset selector is created correctly"""
        presets = ConfigurationManager.PRESETS
        selector = PresetSelector(presets)

        # Should have custom option plus all presets
        assert selector.combo.count() == len(presets) + 1
        assert selector.combo.itemText(0) == "-- Custom --"

        # Should contain all preset names
        preset_names = [selector.combo.itemText(i) for i in range(1, selector.combo.count())]
        for preset_name in presets.keys():
            assert preset_name in preset_names


class TestGridAlignment:
    """Test Fix 9: Visual Alignment Using Grid"""
    
    def setup_method(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])
    
    def test_parameter_widget_grid_layout(self):
        """Test that parameter widgets use grid layout for alignment"""
        param_def = ConfigurationManager.PARAMETERS['concentricPolygonRadius']
        widget = ParameterWidget(param_def)
        
        # Should use QGridLayout
        layout = widget.layout()
        assert isinstance(layout, QtWidgets.QGridLayout)
        
        # Should have fixed column widths
        label = layout.itemAtPosition(0, 0).widget()
        input_field = layout.itemAtPosition(0, 1).widget()
        unit_label = layout.itemAtPosition(0, 2).widget()
        range_label = layout.itemAtPosition(0, 3).widget()
        
        assert isinstance(label, QtWidgets.QLabel)
        assert isinstance(input_field, QtWidgets.QLineEdit)
        assert isinstance(unit_label, QtWidgets.QLabel)
        assert isinstance(range_label, QtWidgets.QLabel)
        
        # Check fixed widths
        assert label.minimumWidth() == 300
        assert input_field.minimumWidth() == 80


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
