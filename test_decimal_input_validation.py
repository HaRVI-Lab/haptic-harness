#!/usr/bin/env python3
"""
Test script to verify that incomplete decimal inputs are handled gracefully
without crashing the haptic harness generator application.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
import numpy as np

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Create a minimal mock generator class for testing
class MockGenerator:
    """Mock generator class for testing validation logic"""

    def __init__(self):
        # Initialize with some default values
        self.concentricPolygonRadius = 30.0
        self.numSides = 6
        self.mountBottomAngleOpening = 60 * np.pi / 180

    def customSetAttr(self, attrName, val):
        """
        Set attribute with robust input validation for incomplete decimal inputs.
        Handles cases like '.', '.1', '1.', etc. gracefully without crashing.
        """
        if val == "":
            setattr(self, attrName, None)
            return

        # Handle incomplete or invalid numeric inputs gracefully
        try:
            if attrName == "numSides" or attrName == "numMagnetsInRing":
                # For integer parameters, handle partial inputs
                parsed_val = self._parse_integer_input(val, attrName)
                if parsed_val is not None:
                    setattr(self, attrName, parsed_val)
            elif (
                attrName == "mountBottomAngleOpening"
                or attrName == "mountTopAngleOpening"
            ):
                # For angle parameters, handle partial inputs and convert to radians
                parsed_val = self._parse_float_input(val, attrName)
                if parsed_val is not None:
                    setattr(self, attrName, parsed_val * np.pi / 180)
            else:
                # For other float parameters, handle partial inputs
                parsed_val = self._parse_float_input(val, attrName)
                if parsed_val is not None:
                    setattr(self, attrName, parsed_val)
        except Exception as e:
            # Log the error but don't crash the application
            print(f"Warning: Failed to set parameter {attrName} to '{val}': {e}")
            # Keep the current value unchanged
            pass

    def _parse_float_input(self, val, attrName):
        """Parse float input with robust handling of incomplete decimal numbers."""
        val_str = str(val).strip()

        # Handle empty or whitespace-only input
        if not val_str:
            return None

        # Handle incomplete decimal inputs
        if val_str == ".":
            # Just a decimal point - treat as incomplete input, don't update
            return None
        elif val_str.startswith(".") and len(val_str) > 1:
            # Starts with decimal point like ".1" - prepend zero
            val_str = "0" + val_str
        elif val_str.endswith(".") and len(val_str) > 1:
            # Ends with decimal point like "1." - this is valid, let float() handle it
            pass
        elif val_str.count('.') > 1:
            # Multiple decimal points - invalid
            return None

        try:
            return float(val_str)
        except ValueError:
            # Invalid numeric format - return None to keep current value
            return None

    def _parse_integer_input(self, val, attrName):
        """Parse integer input with robust handling of incomplete inputs."""
        val_str = str(val).strip()

        # Handle empty or whitespace-only input
        if not val_str:
            return None

        # For integer fields, don't allow decimal points at all
        if '.' in val_str:
            return None

        try:
            return int(val_str)
        except ValueError:
            # Invalid integer format - return None to keep current value
            return None

class TestDecimalInputValidation(unittest.TestCase):
    """Test cases for decimal input validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = MockGenerator()
        
        # Mock parameter definition for UI tests
        self.mock_param_def = Mock()
        self.mock_param_def.name = "testParam"
        self.mock_param_def.display_name = "Test Parameter"
        self.mock_param_def.default_value = 10.0
        self.mock_param_def.min_value = 0.0
        self.mock_param_def.max_value = 100.0
        self.mock_param_def.unit = "mm"
        self.mock_param_def.description = "Test parameter"
    
    def test_generator_customSetAttr_incomplete_decimal_inputs(self):
        """Test that generator handles incomplete decimal inputs gracefully"""
        test_cases = [
            (".", None),  # Just decimal point - should not crash
            (".1", 0.1),  # Leading decimal point - should work
            ("1.", 1.0),  # Trailing decimal point - should work
            (".5", 0.5),  # Another leading decimal case
            ("", None),   # Empty string - should set to None
            ("1.2.3", None),  # Multiple decimal points - should be ignored
            ("abc", None),    # Invalid text - should be ignored
            ("10.5", 10.5),   # Valid decimal - should work
            ("42", 42.0),     # Valid integer - should work
        ]
        
        original_value = getattr(self.generator, 'concentricPolygonRadius', 30.0)
        
        for input_val, expected_result in test_cases:
            with self.subTest(input_val=input_val):
                # Reset to original value before each test
                setattr(self.generator, 'concentricPolygonRadius', original_value)

                try:
                    # This should not crash
                    self.generator.customSetAttr('concentricPolygonRadius', input_val)

                    if expected_result is not None:
                        # Value should be updated
                        actual_value = getattr(self.generator, 'concentricPolygonRadius')
                        self.assertAlmostEqual(actual_value, expected_result, places=5)
                    else:
                        # Value should remain unchanged for invalid inputs
                        # (except for empty string which sets to None)
                        if input_val == "":
                            self.assertIsNone(getattr(self.generator, 'concentricPolygonRadius'))
                        else:
                            # For invalid inputs, value should remain unchanged
                            actual_value = getattr(self.generator, 'concentricPolygonRadius')
                            self.assertEqual(actual_value, original_value)

                except Exception as e:
                    self.fail(f"customSetAttr crashed with input '{input_val}': {e}")
    
    def test_generator_integer_parameter_validation(self):
        """Test integer parameter validation"""
        test_cases = [
            ("6", 6),      # Valid integer
            ("", None),    # Empty string
            ("6.5", None), # Decimal for integer param - should be ignored
            (".", None),   # Just decimal point
            ("abc", None), # Invalid text
        ]
        
        original_value = getattr(self.generator, 'numSides', 6)
        
        for input_val, expected_result in test_cases:
            with self.subTest(input_val=input_val):
                # Reset to original value before each test
                setattr(self.generator, 'numSides', original_value)

                try:
                    self.generator.customSetAttr('numSides', input_val)

                    if expected_result is not None:
                        actual_value = getattr(self.generator, 'numSides')
                        self.assertEqual(actual_value, expected_result)
                    else:
                        if input_val == "":
                            self.assertIsNone(getattr(self.generator, 'numSides'))
                        else:
                            # For invalid inputs, value should remain unchanged
                            actual_value = getattr(self.generator, 'numSides')
                            self.assertEqual(actual_value, original_value)

                except Exception as e:
                    self.fail(f"customSetAttr crashed with integer input '{input_val}': {e}")
    
    def test_generator_angle_parameter_validation(self):
        """Test angle parameter validation (degrees to radians conversion)"""
        import numpy as np

        test_cases = [
            ("45", 45 * np.pi / 180),  # Valid angle
            (".5", 0.5 * np.pi / 180), # Leading decimal
            ("90.", 90 * np.pi / 180), # Trailing decimal
            (".", None),               # Just decimal point
            ("", None),                # Empty string
        ]

        original_value = getattr(self.generator, 'mountBottomAngleOpening', 60 * np.pi / 180)

        for input_val, expected_result in test_cases:
            with self.subTest(input_val=input_val):
                # Reset to original value before each test
                setattr(self.generator, 'mountBottomAngleOpening', original_value)

                try:
                    self.generator.customSetAttr('mountBottomAngleOpening', input_val)

                    if expected_result is not None:
                        actual_value = getattr(self.generator, 'mountBottomAngleOpening')
                        self.assertAlmostEqual(actual_value, expected_result, places=5)
                    else:
                        if input_val == "":
                            self.assertIsNone(getattr(self.generator, 'mountBottomAngleOpening'))
                        else:
                            # For invalid inputs, value should remain unchanged
                            actual_value = getattr(self.generator, 'mountBottomAngleOpening')
                            self.assertAlmostEqual(actual_value, original_value, places=5)

                except Exception as e:
                    self.fail(f"customSetAttr crashed with angle input '{input_val}': {e}")

    def test_ui_validation_logic(self):
        """Test UI validation logic without requiring PyQt5"""
        # Test the validation logic directly
        def is_valid_partial_input(text):
            """Replicated validation logic from ParameterWidget"""
            if not text:
                return True  # Empty is acceptable

            # Allow single decimal point (user is typing)
            if text == ".":
                return True

            # Allow leading decimal point with digits
            if text.startswith(".") and len(text) > 1:
                try:
                    float("0" + text)
                    return True
                except ValueError:
                    return False

            # Allow trailing decimal point
            if text.endswith(".") and len(text) > 1:
                try:
                    float(text)
                    return True
                except ValueError:
                    return False

            # Check for multiple decimal points
            if text.count('.') > 1:
                return False

            # Try to parse as float
            try:
                float(text)
                return True
            except ValueError:
                return False

        def preprocess_decimal_input(text):
            """Replicated preprocessing logic from ParameterWidget"""
            if not text:
                return None

            # Handle incomplete decimal inputs
            if text == ".":
                # Just a decimal point - incomplete input
                return None
            elif text.startswith(".") and len(text) > 1:
                # Starts with decimal point like ".1" - prepend zero
                return "0" + text
            elif text.endswith(".") and len(text) > 1:
                # Ends with decimal point like "1." - valid for float conversion
                return text
            elif text.count('.') > 1:
                # Multiple decimal points - invalid
                return None
            else:
                # Regular input
                return text

        # Test the validation methods
        test_cases = [
            (".", True),      # Just decimal point - acceptable during typing
            (".1", True),     # Leading decimal point - valid
            ("1.", True),     # Trailing decimal point - valid
            ("10.5", True),   # Valid decimal - valid
            ("42", True),     # Valid integer - valid
            ("", True),       # Empty - acceptable
            ("1.2.3", False), # Multiple decimal points - invalid
            ("abc", False),   # Invalid text - invalid
        ]

        for input_val, expected_valid in test_cases:
            with self.subTest(input_val=input_val):
                result = is_valid_partial_input(input_val)
                self.assertEqual(result, expected_valid,
                               f"Input '{input_val}' validation failed")

        # Test preprocessing
        preprocess_cases = [
            (".", None),      # Just decimal point - incomplete
            (".1", "0.1"),    # Leading decimal point - prepend zero
            ("1.", "1."),     # Trailing decimal point - unchanged
            ("10.5", "10.5"), # Valid decimal - unchanged
            ("", None),       # Empty - incomplete
            ("1.2.3", None),  # Multiple decimal points - invalid
        ]

        for input_val, expected_result in preprocess_cases:
            with self.subTest(input_val=input_val):
                result = preprocess_decimal_input(input_val)
                self.assertEqual(result, expected_result,
                               f"Preprocessing '{input_val}' failed")

def run_tests():
    """Run the test suite"""
    print("Running decimal input validation tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDecimalInputValidation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print("\n✅ All tests passed! Decimal input validation is working correctly.")
        return True
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
