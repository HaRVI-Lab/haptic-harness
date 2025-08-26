"""
Tests for PrecisionHandler module
"""

import unittest
from decimal import Decimal
from haptic_harness_generator.core.precision_handler import (
    PrecisionHandler, round_value, format_display, values_equal
)


class TestPrecisionHandler(unittest.TestCase):
    """Test cases for PrecisionHandler class"""
    
    def test_round_value_basic(self):
        """Test basic rounding functionality"""
        # Test cases from task file
        self.assertEqual(round_value(59.999999999), 60.0)
        self.assertEqual(round_value(30.0), 30.0)
        self.assertEqual(round_value(25.995), 26.0)
        
        # Additional edge cases
        self.assertEqual(round_value(0.001), 0.0)
        self.assertEqual(round_value(0.005), 0.01)
        self.assertEqual(round_value(999.995), 1000.0)
        self.assertEqual(round_value(-59.999999), -60.0)
    
    def test_round_value_different_decimals(self):
        """Test rounding with different decimal places"""
        self.assertEqual(round_value(59.999999999, 0), 60.0)
        self.assertEqual(round_value(59.999999999, 1), 60.0)
        self.assertEqual(round_value(59.999999999, 3), 60.0)
        
        self.assertEqual(round_value(25.12345, 0), 25.0)
        self.assertEqual(round_value(25.12345, 1), 25.1)
        self.assertEqual(round_value(25.12345, 3), 25.123)
    
    def test_round_value_string_input(self):
        """Test rounding with string inputs"""
        self.assertEqual(round_value("59.999999999"), 60.0)
        self.assertEqual(round_value("30.0"), 30.0)
        self.assertEqual(round_value("25.995"), 26.0)
    
    def test_round_value_invalid_input(self):
        """Test rounding with invalid inputs"""
        self.assertEqual(round_value(None), 0.0)
        self.assertEqual(round_value("invalid"), 0.0)
    
    def test_format_display_degrees(self):
        """Test display formatting for degrees"""
        self.assertEqual(format_display(60, "degrees"), "60.00°")
        self.assertEqual(format_display(59.999999999, "degrees"), "60.00°")
        self.assertEqual(format_display(30.0, "degrees"), "30.00°")
        self.assertEqual(format_display(0, "degrees"), "0.00°")
        self.assertEqual(format_display(-45, "degrees"), "-45.00°")
    
    def test_format_display_mm(self):
        """Test display formatting for millimeters"""
        self.assertEqual(format_display(30.0, "mm"), "30.00mm")
        self.assertEqual(format_display(25.995, "mm"), "26.00mm")
        self.assertEqual(format_display(0.001, "mm"), "0.00mm")
        self.assertEqual(format_display(999.995, "mm"), "1000.00mm")
    
    def test_format_display_count(self):
        """Test display formatting for count parameters"""
        self.assertEqual(format_display(5, None), "5.00#")
        self.assertEqual(format_display(5, ""), "5.00#")
        self.assertEqual(format_display(10.0, None), "10.00#")
    
    def test_format_display_different_decimals(self):
        """Test display formatting with different decimal places"""
        self.assertEqual(format_display(60, "degrees", 0), "60°")
        self.assertEqual(format_display(60, "degrees", 1), "60.0°")
        self.assertEqual(format_display(60, "degrees", 3), "60.000°")
    
    def test_values_equal(self):
        """Test value comparison with tolerance"""
        self.assertTrue(values_equal(59.999999999, 60.0))
        self.assertTrue(values_equal(30.0, 30.0))
        self.assertTrue(values_equal(25.995, 26.0, tolerance=0.01))
        
        self.assertFalse(values_equal(59.9, 60.0, tolerance=1e-10))
        self.assertTrue(values_equal(59.9, 60.0, tolerance=0.1))
    
    def test_round_config(self):
        """Test configuration dictionary rounding"""
        config = {
            "param1": 59.999999999,
            "param2": 30.0,
            "param3": 25.995,
            "param4": "string_value",
            "param5": None
        }
        
        rounded = PrecisionHandler.round_config(config)
        
        self.assertEqual(rounded["param1"], 60.0)
        self.assertEqual(rounded["param2"], 30.0)
        self.assertEqual(rounded["param3"], 26.0)
        self.assertEqual(rounded["param4"], "string_value")
        self.assertEqual(rounded["param5"], None)
    
    def test_validate_precision(self):
        """Test precision validation"""
        self.assertTrue(PrecisionHandler.validate_precision(60.00, 2))
        self.assertTrue(PrecisionHandler.validate_precision(60.0, 2))
        self.assertTrue(PrecisionHandler.validate_precision(60, 2))
        
        self.assertTrue(PrecisionHandler.validate_precision(60.123, 3))
        self.assertFalse(PrecisionHandler.validate_precision(60.123, 2))
    
    def test_decimal_accuracy(self):
        """Test that Decimal provides accurate rounding"""
        # This would fail with regular float rounding
        value = 0.1 + 0.1 + 0.1  # 0.30000000000000004 in float
        rounded = round_value(value)
        self.assertEqual(rounded, 0.3)
        
        # Test with very precise values
        precise_value = Decimal('59.999999999999999999')
        rounded = round_value(float(precise_value))
        self.assertEqual(rounded, 60.0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def test_convenience_round_value(self):
        """Test convenience round_value function"""
        self.assertEqual(round_value(59.999999999), 60.0)
        self.assertEqual(round_value(30.0), 30.0)
    
    def test_convenience_format_display(self):
        """Test convenience format_display function"""
        self.assertEqual(format_display(60, "degrees"), "60.00°")
        self.assertEqual(format_display(30.0, "mm"), "30.00mm")
    
    def test_convenience_values_equal(self):
        """Test convenience values_equal function"""
        self.assertTrue(values_equal(59.999999999, 60.0))
        self.assertFalse(values_equal(59.9, 60.0))


if __name__ == '__main__':
    unittest.main()
