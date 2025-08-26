"""
Core UI improvements test suite
Tests the modular components without requiring full GUI dependencies
"""
import pytest
import sys
import os
from PyQt5 import QtWidgets, QtCore

# Add the package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only the core components
from config_manager import ConfigurationManager
from validation_engine import ValidationEngine
from ui_helpers import ParameterWidget, PresetSelector


class TestConfigurationManager:
    """Test configuration manager improvements"""
    
    def test_parameter_display_formatting(self):
        """Test Fix 3: Parameter display formatting improvements"""
        # Test parameter with ui_number > 0
        display = ConfigurationManager.get_parameter_display('concentricPolygonRadius')
        assert display == "[1] Concentric Polygon Radius"
        
        # Test parameter with ui_number = 0 (should not show [0])
        display = ConfigurationManager.get_parameter_display('numSides')
        assert display == "Number of Sides"  # No [0] bracket
        
        # Test parameter with ui_number = 0 for foamThickness
        display = ConfigurationManager.get_parameter_display('foamThickness')
        assert display == "Foam Thickness"  # No [0] bracket
    
    def test_preset_configurations_exist(self):
        """Test that all required presets exist"""
        presets = ConfigurationManager.PRESETS
        
        # Should have the main presets
        assert "Standard 6-sided" in presets
        assert "Standard 4-sided" in presets
        assert "Compact 4-sided" in presets
        
        # Each preset should have all required parameters
        for preset_name, config in presets.items():
            assert 'concentricPolygonRadius' in config
            assert 'numSides' in config
            assert 'slotWidth' in config


class TestValidationEngine:
    """Test validation engine improvements"""
    
    def setup_method(self):
        self.validator = ValidationEngine()
    
    def test_comprehensive_suggestions(self):
        """Test Fix 7: Complete suggestion coverage"""
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
        
        # Should have suggestions for errors
        assert len(result.suggestions) > 0
        
        # Suggestions should be specific and helpful
        for suggestion in result.suggestions:
            assert len(suggestion) > 10  # Not just generic text
    
    def test_tolerance_in_suggestions(self):
        """Test Fix 8: Tolerance in suggestions"""
        config = {
            'concentricPolygonRadius': 30,
            'slotWidth': 35,  # Too wide
            'numSides': 6
        }
        
        result = self.validator.validate_complete(config)
        
        # Should have suggestions with safety margins
        assert len(result.suggestions) > 0
        
        # Test the safety margin calculation method
        safe_value = self.validator._calculate_safe_value(10.0, 'dimension')
        assert safe_value == 11.0  # 10% margin for dimensions
        
        safe_clearance = self.validator._calculate_safe_value(5.0, 'clearance')
        assert safe_clearance == 6.0  # 20% margin for clearances
    
    def test_error_specific_suggestions(self):
        """Test that specific error types get specific suggestions"""
        # Test range validation
        config = {
            'concentricPolygonRadius': 5,  # Below minimum
            'slotWidth': 50,  # Above maximum
        }
        
        result = self.validator.validate_complete(config)
        assert not result.is_valid
        assert len(result.errors) >= 2  # Should have range errors


class TestParameterWidget:
    """Test parameter widget improvements"""
    
    def setup_method(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])
    
    def test_programmatic_update_flag(self):
        """Test Fix 1: Programmatic update flag prevents unwanted signals"""
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
    
    def test_grid_layout_alignment(self):
        """Test Fix 9: Grid layout for perfect alignment"""
        param_def = ConfigurationManager.PARAMETERS['concentricPolygonRadius']
        widget = ParameterWidget(param_def)
        
        # Should use QGridLayout
        layout = widget.layout()
        assert isinstance(layout, QtWidgets.QGridLayout)
        
        # Should have widgets in correct grid positions
        label = layout.itemAtPosition(0, 0).widget()
        input_field = layout.itemAtPosition(0, 1).widget()
        unit_label = layout.itemAtPosition(0, 2).widget()
        range_label = layout.itemAtPosition(0, 3).widget()
        
        assert isinstance(label, QtWidgets.QLabel)
        assert isinstance(input_field, QtWidgets.QLineEdit)
        assert isinstance(unit_label, QtWidgets.QLabel)
        assert isinstance(range_label, QtWidgets.QLabel)
        
        # Check fixed widths for alignment
        assert label.minimumWidth() == 300
        assert input_field.minimumWidth() == 80
        assert unit_label.minimumWidth() == 40
        assert range_label.minimumWidth() == 100
    
    def test_enhanced_range_label(self):
        """Test Fix 3: Enhanced range label styling"""
        param_def = ConfigurationManager.PARAMETERS['concentricPolygonRadius']
        widget = ParameterWidget(param_def)
        
        # Find the range label
        layout = widget.layout()
        range_label = layout.itemAtPosition(0, 3).widget()
        
        # Should have enhanced styling
        style = range_label.styleSheet()
        assert "border-radius" in style
        assert "background-color" in style
        assert "border:" in style
        
        # Should have tooltip
        assert range_label.toolTip() != ""
        assert "Valid range:" in range_label.toolTip()


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
    
    def test_custom_mode_setting(self):
        """Test setting custom mode"""
        presets = ConfigurationManager.PRESETS
        selector = PresetSelector(presets)
        
        # Set to a preset first
        selector.combo.setCurrentText("Standard 6-sided")
        assert selector.combo.currentText() == "Standard 6-sided"
        
        # Set to custom
        selector.set_custom()
        assert selector.combo.currentText() == "-- Custom --"


class TestImplementationCompleteness:
    """Test that all fixes from the guide are implemented"""
    
    def test_all_parameter_definitions_exist(self):
        """Test that all parameters have proper definitions"""
        params = ConfigurationManager.PARAMETERS
        
        # Should have all the main parameters
        required_params = [
            'concentricPolygonRadius', 'tactorRadius', 'magnetRingRadius',
            'numSides', 'slotWidth', 'magnetRadius', 'magnetThickness'
        ]
        
        for param in required_params:
            assert param in params
            param_def = params[param]
            assert hasattr(param_def, 'display_name')
            assert hasattr(param_def, 'ui_number')
            assert hasattr(param_def, 'min_value')
            assert hasattr(param_def, 'max_value')
            assert hasattr(param_def, 'tooltip')
    
    def test_validation_engine_methods_exist(self):
        """Test that validation engine has all required methods"""
        validator = ValidationEngine()
        
        # Should have the new methods
        assert hasattr(validator, '_calculate_safe_value')
        assert hasattr(validator, '_suggest_increase_parameter')
        assert hasattr(validator, '_suggest_decrease_parameter')
        assert hasattr(validator, '_suggest_tolerance_fix')
        
        # Test safety margin calculation
        safe_value = validator._calculate_safe_value(10.0, 'dimension')
        assert safe_value > 10.0  # Should add margin


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
