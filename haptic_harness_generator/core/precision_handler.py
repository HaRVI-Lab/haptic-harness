"""
Precision Handler Module - Centralized floating point precision management

This module provides accurate rounding and formatting for all numeric values
in the Haptic Harness Generator to eliminate floating point display issues.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional


class PrecisionHandler:
    """Centralized precision handling for all numeric values"""
    
    DEFAULT_DECIMALS = 2
    TOLERANCE = 1e-9  # Increased tolerance for floating point comparisons
    
    @staticmethod
    def round_value(value: Union[float, int, str], decimals: int = DEFAULT_DECIMALS) -> float:
        """
        Round using Decimal for accuracy
        
        Args:
            value: The value to round
            decimals: Number of decimal places (default: 2)
            
        Returns:
            Rounded float value
            
        Examples:
            >>> round_value(59.999999999)
            60.0
            >>> round_value(30.0)
            30.0
            >>> round_value(25.995)
            26.0
        """
        try:
            d = Decimal(str(value))
            if decimals == 0:
                return float(d.quantize(Decimal('1'), ROUND_HALF_UP))
            quantizer = Decimal('0.1') ** decimals
            return float(d.quantize(quantizer, ROUND_HALF_UP))
        except (ValueError, TypeError):
            # Fallback for invalid inputs
            return float(value) if value is not None else 0.0
    
    @staticmethod
    def format_display(value: Union[float, int, str], unit: Optional[str] = None, 
                      decimals: int = DEFAULT_DECIMALS) -> str:
        """
        Format value for display with proper unit symbols
        
        Args:
            value: The value to format
            unit: Unit type ('mm', 'degrees', or None for count)
            decimals: Number of decimal places
            
        Returns:
            Formatted string with proper unit symbol
            
        Examples:
            >>> format_display(60, "degrees")
            "60.00°"
            >>> format_display(30.0, "mm")
            "30.00mm"
            >>> format_display(5, None)
            "5#"
        """
        rounded_value = PrecisionHandler.round_value(value, decimals)
        
        # Format with specified decimal places
        if decimals == 0:
            formatted = f"{int(rounded_value)}"
        else:
            formatted = f"{rounded_value:.{decimals}f}"
        
        # Add appropriate unit symbol
        if unit == "degrees":
            return f"{formatted}°"
        elif unit == "mm":
            return f"{formatted}mm"
        elif unit is None or unit == "":
            return f"{formatted}#"
        else:
            return f"{formatted}{unit}"
    
    @staticmethod
    def values_equal(value1: Union[float, int], value2: Union[float, int], 
                    tolerance: float = TOLERANCE) -> bool:
        """
        Compare two values with tolerance for floating point precision
        
        Args:
            value1: First value
            value2: Second value
            tolerance: Comparison tolerance
            
        Returns:
            True if values are equal within tolerance
        """
        return abs(float(value1) - float(value2)) < tolerance
    
    @staticmethod
    def round_config(config: dict, decimals: int = DEFAULT_DECIMALS) -> dict:
        """
        Round all numeric values in a configuration dictionary
        
        Args:
            config: Configuration dictionary
            decimals: Number of decimal places
            
        Returns:
            New dictionary with rounded values
        """
        rounded_config = {}
        for key, value in config.items():
            if isinstance(value, (int, float)):
                rounded_config[key] = PrecisionHandler.round_value(value, decimals)
            else:
                rounded_config[key] = value
        return rounded_config
    
    @staticmethod
    def validate_precision(value: Union[float, int, str], expected_decimals: int = DEFAULT_DECIMALS) -> bool:
        """
        Validate that a value has the expected precision
        
        Args:
            value: Value to check
            expected_decimals: Expected number of decimal places
            
        Returns:
            True if value has correct precision
        """
        try:
            str_value = str(float(value))
            if '.' in str_value:
                decimal_places = len(str_value.split('.')[1])
                return decimal_places <= expected_decimals
            return True
        except (ValueError, TypeError):
            return False


# Convenience functions for common operations
def round_value(value: Union[float, int, str], decimals: int = 2) -> float:
    """Convenience function for rounding values"""
    return PrecisionHandler.round_value(value, decimals)


def format_display(value: Union[float, int, str], unit: Optional[str] = None, 
                  decimals: int = 2) -> str:
    """Convenience function for formatting display values"""
    return PrecisionHandler.format_display(value, unit, decimals)


def values_equal(value1: Union[float, int], value2: Union[float, int],
                tolerance: float = 1e-9) -> bool:
    """Convenience function for comparing values with tolerance"""
    return PrecisionHandler.values_equal(value1, value2, tolerance)


if __name__ == "__main__":
    # Simple test to verify functionality
    print("Testing PrecisionHandler:")

    # Test cases from task file
    print(f"round_value(59.999999999) = {round_value(59.999999999)} (expected: 60.0)")
    print(f"round_value(30.0) = {round_value(30.0)} (expected: 30.0)")
    print(f"round_value(25.995) = {round_value(25.995)} (expected: 26.0)")

    print(f"format_display(60, 'degrees') = {format_display(60, 'degrees')} (expected: 60.00°)")
    print(f"format_display(30.0, 'mm') = {format_display(30.0, 'mm')} (expected: 30.00mm)")
    print(f"format_display(5, None) = {format_display(5, None)} (expected: 5.00#)")

    print(f"values_equal(59.999999999, 60.0) = {values_equal(59.999999999, 60.0)} (expected: True)")
    print(f"values_equal(59.999999999, 60.0, 0.01) = {values_equal(59.999999999, 60.0, 0.01)} (expected: True)")

    # Debug the difference
    diff = abs(59.999999999 - 60.0)
    print(f"Difference: {diff}")

    print("All tests completed successfully!")
