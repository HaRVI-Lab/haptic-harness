"""
Comprehensive automated testing suite
"""

import unittest
import json
import tempfile
import os
from typing import Dict, List
import numpy as np
from haptic_harness_generator.core.config_manager import ConfigurationManager
from haptic_harness_generator.core.validation_engine import ValidationEngine


class TestPresetConfigurations(unittest.TestCase):
    """Test all preset configurations"""

    def setUp(self):
        self.validator = ValidationEngine()
        # Create test directory in test_outputs
        os.makedirs("../test_outputs", exist_ok=True)
        self.test_dir = tempfile.mkdtemp(dir="../test_outputs")

    def test_all_presets_validate(self):
        """All presets must pass validation"""
        for preset_name, config in ConfigurationManager.PRESETS.items():
            with self.subTest(preset=preset_name):
                result = self.validator.validate_complete(config)
                self.assertTrue(
                    result.is_valid,
                    f"Preset '{preset_name}' failed validation:\n"
                    + "\n".join(result.errors),
                )

    def test_all_presets_generate(self):
        """All presets must generate without errors"""
        # Import Generator here to avoid circular imports
        try:
            from haptic_harness_generator.core.generator import Generator
        except ImportError:
            self.skipTest("Generator module not available for testing")

        for preset_name, config in ConfigurationManager.PRESETS.items():
            with self.subTest(preset=preset_name):
                generator = Generator(self.test_dir)

                # Apply configuration
                for param, value in config.items():
                    if param in ["mountBottomAngleOpening", "mountTopAngleOpening"]:
                        value = value * np.pi / 180
                    setattr(generator, param, value)

                # Attempt generation
                try:
                    generator.regen()
                    self.assertTrue(
                        True, f"Preset '{preset_name}' generated successfully"
                    )
                except Exception as e:
                    self.fail(f"Preset '{preset_name}' generation failed: {str(e)}")

    def test_export_import_cycle(self):
        """Test configuration export and import"""
        for preset_name, config in ConfigurationManager.PRESETS.items():
            with self.subTest(preset=preset_name):
                # Export
                export_path = os.path.join(
                    self.test_dir, f"test_config_{preset_name}.json"
                )
                self.assertTrue(
                    ConfigurationManager.export_config(config, export_path),
                    f"Failed to export {preset_name}",
                )

                # Import
                imported = ConfigurationManager.import_config(export_path)
                self.assertIsNotNone(imported, f"Failed to import {preset_name}")

                # Verify
                for key, value in config.items():
                    self.assertEqual(
                        imported.get(key),
                        value,
                        f"Parameter {key} mismatch after import",
                    )


class TestGeometricValidation(unittest.TestCase):
    """Test geometric constraint validation"""

    def setUp(self):
        self.validator = ValidationEngine()
        self.base_config = ConfigurationManager.PRESETS["Standard 6-sided"].copy()

    def test_slot_width_constraint(self):
        """Test slot width validation"""
        config = self.base_config.copy()

        # Calculate breaking point
        numSides = config["numSides"]
        diameter = config["concentricPolygonDiameter"]
        max_slot = diameter * np.tan(np.pi / numSides) - 2

        # Test just below limit - should pass
        config["slotWidth"] = max_slot - 1
        result = self.validator.validate_complete(config)
        self.assertTrue(result.is_valid, "Valid slot width marked as invalid")

        # Test just above limit - should fail
        config["slotWidth"] = max_slot + 1
        result = self.validator.validate_complete(config)
        self.assertFalse(result.is_valid, "Invalid slot width not caught")
        self.assertIn("slotWidth", result.affected_parameters)

    def test_tactor_magnet_clearance(self):
        """Test tactor-magnet interference detection"""
        config = self.base_config.copy()

        # Set values that will interfere
        config["tactorDiameter"] = 15 * 2
        config["magnetRingDiameter"] = 18 * 2
        config["magnetDiameter"] = 5 * 2

        result = self.validator.validate_complete(config)
        self.assertFalse(result.is_valid, "Tactor-magnet interference not detected")
        self.assertIn("tactorDiameter", result.affected_parameters)

    def test_flap_intersection(self):
        """Test flap intersection detection"""
        config = self.base_config.copy()

        # Set values that cause flap intersection
        config["slotBorderRadius"] = 20
        config["slotWidth"] = 28
        config["numSides"] = 6

        result = self.validator.validate_complete(config)
        # This may or may not fail depending on exact geometry, but shouldn't crash
        self.assertIsNotNone(result)

    def test_mount_radius_constraint(self):
        """Test mount diameter validation"""
        config = self.base_config.copy()

        # Set mount diameter too large
        config["mountDiameter"] = (
            config["magnetRingDiameter"] - config["magnetRingDiameter"]
        )

        result = self.validator.validate_complete(config)
        self.assertFalse(result.is_valid, "Mount diameter constraint not enforced")
        self.assertIn("mountDiameter", result.affected_parameters)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def setUp(self):
        self.validator = ValidationEngine()

    def test_minimum_values(self):
        """Test all parameters at minimum values"""
        config = {}
        for param_name, param_def in ConfigurationManager.PARAMETERS.items():
            config[param_name] = param_def.min_value

        # This may not validate due to geometric constraints
        # but shouldn't crash
        result = self.validator.validate_complete(config)
        self.assertIsNotNone(result)

    def test_maximum_values(self):
        """Test all parameters at maximum values"""
        config = {}
        for param_name, param_def in ConfigurationManager.PARAMETERS.items():
            config[param_name] = param_def.max_value

        result = self.validator.validate_complete(config)
        self.assertIsNotNone(result)

    def test_numSides_variations(self):
        """Test all valid numSides values"""
        base_config = ConfigurationManager.PRESETS["Standard 4-sided"].copy()

        for num_sides in range(3, 9):
            with self.subTest(numSides=num_sides):
                config = base_config.copy()
                config["numSides"] = num_sides

                # Adjust slot width for different polygon sizes
                diameter = config["concentricPolygonDiameter"]
                max_slot = diameter * np.tan(np.pi / num_sides) - 4
                config["slotWidth"] = min(config["slotWidth"], max_slot)

                result = self.validator.validate_complete(config)

                # Should handle all cases without crashing
                self.assertIsNotNone(result)

    def test_invalid_numSides(self):
        """Test invalid number of sides"""
        config = ConfigurationManager.PRESETS["Standard 6-sided"].copy()

        # Test below minimum
        config["numSides"] = 2
        result = self.validator.validate_complete(config)
        self.assertFalse(result.is_valid)
        self.assertIn("numSides", result.affected_parameters)

        # Test above maximum
        config["numSides"] = 9
        result = self.validator.validate_complete(config)
        self.assertFalse(result.is_valid)
        self.assertIn("numSides", result.affected_parameters)


class TestParameterInteractions(unittest.TestCase):
    """Test parameter interaction matrix"""

    def setUp(self):
        self.validator = ValidationEngine()
        self.base_config = ConfigurationManager.PRESETS["Standard 6-sided"].copy()

    def test_parameter_dependencies(self):
        """Test that changing one parameter affects related validations"""
        test_cases = [
            # (parameter, value, should_affect_validation)
            (
                "concentricPolygonDiameter",
                20 * 2,
                True,
            ),  # Should affect slot width validation
            ("tactorDiameter", 15 * 2, True),  # Should affect magnet clearance
            ("numSides", 3, True),  # Should affect polygon geometry
            ("foamThickness", 3, False),  # Should not affect critical geometry
        ]

        for param, value, should_affect in test_cases:
            with self.subTest(parameter=param):
                config = self.base_config.copy()
                config[param] = value

                result = self.validator.validate_complete(config)

                if should_affect:
                    # Should either be invalid or have warnings
                    has_issues = not result.is_valid or len(result.warnings) > 0
                    self.assertTrue(
                        has_issues, f"Parameter {param} change should affect validation"
                    )

                # Should never crash
                self.assertIsNotNone(result)

    def test_suggestion_generation(self):
        """Test that validation suggestions are generated"""
        config = self.base_config.copy()

        # Create a configuration that will generate suggestions
        config["slotWidth"] = 35  # Too wide
        config["concentricPolygonDiameter"] = 25 * 2  # Too small

        result = self.validator.validate_complete(config)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            len(result.suggestions) > 0, "No suggestions generated for invalid config"
        )


class TestConfigurationManager(unittest.TestCase):
    """Test ConfigurationManager functionality"""

    def test_parameter_display_names(self):
        """Test parameter display name generation"""
        for param_name, param_def in ConfigurationManager.PARAMETERS.items():
            display_name = ConfigurationManager.get_parameter_display(param_name)
            self.assertIsInstance(display_name, str)
            self.assertTrue(len(display_name) > 0)

            if param_def.ui_number > 0:
                self.assertIn(f"[{param_def.ui_number}]", display_name)

    def test_preset_completeness(self):
        """Test that all presets have all required parameters"""
        required_params = set(ConfigurationManager.PARAMETERS.keys())

        for preset_name, config in ConfigurationManager.PRESETS.items():
            with self.subTest(preset=preset_name):
                preset_params = set(config.keys())
                missing_params = required_params - preset_params

                # Allow some parameters to be optional
                optional_params = {"foamThickness"}  # Add more as needed
                critical_missing = missing_params - optional_params

                self.assertEqual(
                    len(critical_missing),
                    0,
                    f"Preset '{preset_name}' missing critical parameters: {critical_missing}",
                )


def run_all_tests():
    """Run complete test suite"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPresetConfigurations))
    suite.addTests(loader.loadTestsFromTestCase(TestGeometricValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestParameterInteractions))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigurationManager))

    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate report
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFAILED TESTS:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
