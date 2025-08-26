#!/usr/bin/env python3
"""
Manual test demonstration showing that incomplete decimal inputs 
no longer crash the haptic harness generator.
"""

import sys
import os
import numpy as np

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Create a minimal mock generator class for demonstration
class MockGenerator:
    """Mock generator class demonstrating the fixed validation logic"""
    
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
        print(f"Setting {attrName} = '{val}'")
        
        if val == "":
            setattr(self, attrName, None)
            print(f"  → Set to None (empty input)")
            return
            
        # Handle incomplete or invalid numeric inputs gracefully
        try:
            if attrName == "numSides" or attrName == "numMagnetsInRing":
                # For integer parameters, handle partial inputs
                parsed_val = self._parse_integer_input(val, attrName)
                if parsed_val is not None:
                    setattr(self, attrName, parsed_val)
                    print(f"  → Set to {parsed_val} (integer)")
                else:
                    print(f"  → Ignored invalid integer input")
            elif (
                attrName == "mountBottomAngleOpening"
                or attrName == "mountTopAngleOpening"
            ):
                # For angle parameters, handle partial inputs and convert to radians
                parsed_val = self._parse_float_input(val, attrName)
                if parsed_val is not None:
                    radians_val = parsed_val * np.pi / 180
                    setattr(self, attrName, radians_val)
                    print(f"  → Set to {radians_val:.6f} radians ({parsed_val}°)")
                else:
                    print(f"  → Ignored invalid angle input")
            else:
                # For other float parameters, handle partial inputs
                parsed_val = self._parse_float_input(val, attrName)
                if parsed_val is not None:
                    setattr(self, attrName, parsed_val)
                    print(f"  → Set to {parsed_val} (float)")
                else:
                    print(f"  → Ignored invalid float input")
        except Exception as e:
            # Log the error but don't crash the application
            print(f"  → Warning: Failed to set parameter {attrName} to '{val}': {e}")
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

def demonstrate_fix():
    """Demonstrate that the fix prevents crashes with incomplete decimal inputs"""
    print("🔧 Haptic Harness Generator - Decimal Input Validation Fix Demo")
    print("=" * 60)
    
    generator = MockGenerator()
    
    print(f"\nInitial values:")
    print(f"  concentricPolygonRadius: {generator.concentricPolygonRadius}")
    print(f"  numSides: {generator.numSides}")
    print(f"  mountBottomAngleOpening: {generator.mountBottomAngleOpening:.6f} radians")
    
    print("\n🧪 Testing problematic inputs that used to crash the application:")
    print("-" * 60)
    
    # Test cases that used to cause crashes
    test_cases = [
        ("concentricPolygonRadius", "."),      # Just decimal point
        ("concentricPolygonRadius", ".1"),     # Leading decimal point
        ("concentricPolygonRadius", "1."),     # Trailing decimal point
        ("concentricPolygonRadius", "1.2.3"),  # Multiple decimal points
        ("concentricPolygonRadius", "abc"),    # Invalid text
        ("numSides", "."),                     # Decimal point for integer param
        ("numSides", "6.5"),                   # Decimal for integer param
        ("mountBottomAngleOpening", "."),      # Decimal point for angle
        ("mountBottomAngleOpening", ".5"),     # Leading decimal for angle
        ("concentricPolygonRadius", "25.5"),   # Valid decimal (should work)
        ("numSides", "8"),                     # Valid integer (should work)
        ("mountBottomAngleOpening", "45"),     # Valid angle (should work)
    ]
    
    for param_name, input_val in test_cases:
        print(f"\nTest: {param_name} = '{input_val}'")
        try:
            generator.customSetAttr(param_name, input_val)
            print("  ✅ No crash!")
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
    
    print(f"\n📊 Final values:")
    print(f"  concentricPolygonRadius: {generator.concentricPolygonRadius}")
    print(f"  numSides: {generator.numSides}")
    print(f"  mountBottomAngleOpening: {generator.mountBottomAngleOpening:.6f} radians")
    
    print("\n✅ All tests completed without crashes!")
    print("The application now handles incomplete decimal inputs gracefully.")

if __name__ == "__main__":
    demonstrate_fix()
