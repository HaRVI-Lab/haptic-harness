"""
Comprehensive validation engine with detailed testing
"""
import numpy as np
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from haptic_harness_generator.core.config_manager import ConfigurationManager
from haptic_harness_generator.core.precision_handler import PrecisionHandler, values_equal

@dataclass
class ValidationResult:
    """Detailed validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    affected_parameters: Set[str]
    suggestions: List[str]

class ValidationEngine:
    """Advanced validation with detailed feedback"""
    
    def __init__(self):
        self.tolerance = 1.0  # mm tolerance for manufacturing
        self.critical_errors = []
        self.warnings = []
        self.affected_params = set()
    
    def validate_complete(self, config: Dict) -> ValidationResult:
        """Complete validation with all checks"""

        # Reset state
        self.critical_errors = []
        self.warnings = []
        self.affected_params = set()
        suggestions = []

        # Round all values before validation to ensure precision consistency
        rounded_config = PrecisionHandler.round_config(config)

        # Run validation stages
        self._validate_basic_ranges(rounded_config)
        self._validate_geometric_constraints(rounded_config)
        self._validate_manufacturing_constraints(rounded_config)
        self._validate_assembly_constraints(rounded_config)

        # Generate suggestions
        if self.critical_errors:
            suggestions = self._generate_fix_suggestions(rounded_config)

        return ValidationResult(
            is_valid=len(self.critical_errors) == 0,
            errors=self.critical_errors,
            warnings=self.warnings,
            affected_parameters=self.affected_params,
            suggestions=suggestions
        )
    
    def _validate_basic_ranges(self, config: Dict):
        """Validate all parameters are within defined ranges"""
        # Check if configuration is empty or has too few parameters
        if len(config) == 0:
            self.critical_errors.append("Configuration is empty. Please provide parameter values.")
            return

        # Check for critical missing parameters
        critical_params = ['numSides', 'concentricPolygonRadius', 'tactorRadius', 'magnetRingRadius']
        missing_critical = [p for p in critical_params if p not in config]
        if missing_critical:
            self.critical_errors.append(
                f"Missing critical parameters: {', '.join(missing_critical)}"
            )
            self.affected_params.update(missing_critical)

        for param_name, param_def in ConfigurationManager.PARAMETERS.items():
            if param_name in config:
                value = config[param_name]
                # Use tolerance-based comparison for floating point values
                if value < param_def.min_value and not values_equal(value, param_def.min_value):
                    self.critical_errors.append(
                        f"{ConfigurationManager.get_parameter_display(param_name)}: "
                        f"Value {value:.2f}{param_def.unit} below minimum {param_def.min_value:.2f}{param_def.unit}"
                    )
                    self.affected_params.add(param_name)
                elif value > param_def.max_value and not values_equal(value, param_def.max_value):
                    self.critical_errors.append(
                        f"{ConfigurationManager.get_parameter_display(param_name)}: "
                        f"Value {value:.2f}{param_def.unit} above maximum {param_def.max_value:.2f}{param_def.unit}"
                    )
                    self.affected_params.add(param_name)
    
    def _validate_geometric_constraints(self, config: Dict):
        """Detailed geometric validation"""
        # Extract values with defaults
        numSides = config.get('numSides', 6)
        concentricPolygonRadius = config.get('concentricPolygonRadius', 30)
        slotWidth = config.get('slotWidth', 26)
        slotBorderRadius = config.get('slotBorderRadius', 10)
        tactorRadius = config.get('tactorRadius', 10)
        magnetRadius = config.get('magnetRadius', 5)
        magnetRingRadius = config.get('magnetRingRadius', 20)
        distanceBetweenMagnetsInClip = config.get('distanceBetweenMagnetsInClip', 15)
        distanceBetweenMagnetClipAndPolygonEdge = config.get('distanceBetweenMagnetClipAndPolygonEdge', 3)
        distanceBetweenMagnetClipAndSlot = config.get('distanceBetweenMagnetClipAndSlot', 3)
        slotHeight = config.get('slotHeight', 1.5)
        magnetClipRingThickness = config.get('magnetClipRingThickness', 1.5)
        mountRadius = config.get('mountRadius', 13)
        mountBottomAngleOpening = config.get('mountBottomAngleOpening', 60)
        mountTopAngleOpening = config.get('mountTopAngleOpening', 45)
        strapClipRadius = config.get('strapClipRadius', 1)
        strapClipRim = config.get('strapClipRim', 2)
        numMagnetsInRing = config.get('numMagnetsInRing', 6)
        
        # Validation 1: Number of sides
        if numSides < 3 or numSides > 8:
            self.critical_errors.append(
                f"{ConfigurationManager.get_parameter_display('numSides')}: "
                f"Must be 3-8. (2-sided creates unstable geometry). Recommended: 4 or 6 sides for wrist devices."
            )
            self.affected_params.add('numSides')
        
        # Validation 2: Tactor vs polygon radius
        if tactorRadius >= concentricPolygonRadius:
            self.critical_errors.append(
                f"{ConfigurationManager.get_parameter_display('tactorRadius')} "
                f"({tactorRadius}mm) must be smaller than "
                f"{ConfigurationManager.get_parameter_display('concentricPolygonRadius')} "
                f"({concentricPolygonRadius}mm)"
            )
            self.affected_params.update(['tactorRadius', 'concentricPolygonRadius'])
        
        # Validation 3: Mount radius vs magnet configuration
        if mountRadius > magnetRingRadius - magnetRadius - self.tolerance:
            max_mount = magnetRingRadius - magnetRadius - self.tolerance
            self.critical_errors.append(
                f"{ConfigurationManager.get_parameter_display('mountRadius')} "
                f"({mountRadius}mm) too large. Maximum: {max_mount:.1f}mm"
            )
            self.affected_params.update(['mountRadius', 'magnetRingRadius', 'magnetRadius'])
        
        # Validation 4: Angle constraints
        if mountBottomAngleOpening >= 270:  # 3*PI/2 in degrees
            self.critical_errors.append(
                f"{ConfigurationManager.get_parameter_display('mountBottomAngleOpening')} "
                f"must be less than 270 degrees"
            )
            self.affected_params.add('mountBottomAngleOpening')
        
        if mountTopAngleOpening >= 270:
            self.critical_errors.append(
                f"{ConfigurationManager.get_parameter_display('mountTopAngleOpening')} "
                f"must be less than 270 degrees"
            )
            self.affected_params.add('mountTopAngleOpening')
        
        # Validation 5: Magnet spacing
        if distanceBetweenMagnetsInClip < 2 * magnetRadius + self.tolerance:
            min_distance = 2 * magnetRadius + self.tolerance
            self.critical_errors.append(
                f"{ConfigurationManager.get_parameter_display('distanceBetweenMagnetsInClip')} "
                f"({distanceBetweenMagnetsInClip}mm) too small. Minimum: {min_distance:.1f}mm"
            )
            self.affected_params.update(['distanceBetweenMagnetsInClip', 'magnetRadius'])
        
        # Validation 6: Polygon edge vs magnet configuration
        polygon_edge = 2 * concentricPolygonRadius * np.tan(np.pi / numSides)
        min_edge_for_magnets = 2 * magnetRadius + 2 * self.tolerance + distanceBetweenMagnetsInClip
        if polygon_edge < min_edge_for_magnets:
            self.critical_errors.append(
                f"Polygon edge ({polygon_edge:.1f}mm) too short for magnet configuration. "
                f"Minimum needed: {min_edge_for_magnets:.1f}mm"
            )
            self.affected_params.update(['concentricPolygonRadius', 'numSides', 'magnetRadius', 'distanceBetweenMagnetsInClip'])
        
        # Validation 7: Strap clip constraints
        if strapClipRadius > strapClipRim:
            self.critical_errors.append(
                f"{ConfigurationManager.get_parameter_display('strapClipRadius')} "
                f"({strapClipRadius}mm) cannot be larger than "
                f"{ConfigurationManager.get_parameter_display('strapClipRim')} ({strapClipRim}mm)"
            )
            self.affected_params.update(['strapClipRadius', 'strapClipRim'])
        
        # Validation 8: Number of magnets constraint
        if numMagnetsInRing > 25:
            self.critical_errors.append(
                f"{ConfigurationManager.get_parameter_display('numMagnetsInRing')} "
                f"must be at most 25"
            )
            self.affected_params.add('numMagnetsInRing')
        
        # Use ConfigurationManager's geometric validation for complex constraints
        geo_errors, geo_params = ConfigurationManager._validate_geometry(config)
        self.critical_errors.extend(geo_errors)
        self.affected_params.update(geo_params)
    
    def _validate_manufacturing_constraints(self, config: Dict):
        """Check manufacturing feasibility"""
        # Minimum wall thickness for 3D printing
        min_wall = 0.5  # mm
        
        thin_wall_params = [
            'magnetClipThickness', 'magnetClipRingThickness', 
            'mountShellThickness', 'strapClipThickness'
        ]
        
        for param in thin_wall_params:
            if param in config and config[param] < min_wall:
                self.warnings.append(
                    f"{ConfigurationManager.get_parameter_display(param)} "
                    f"({config[param]}mm) may be too thin for reliable 3D printing. "
                    f"Recommended minimum: {min_wall}mm"
                )
    
    def _validate_assembly_constraints(self, config: Dict):
        """Check if parts can be assembled"""
        # Check minimum tolerances for assembly
        min_tolerance_params = [
            'distanceBetweenMagnetsInClip', 'distanceBetweenMagnetClipAndSlot',
            'distanceBetweenMagnetClipAndPolygonEdge', 'distanceBetweenStrapsInClip'
        ]
        
        for param in min_tolerance_params:
            if param in config and config[param] < self.tolerance:
                self.critical_errors.append(
                    f"{ConfigurationManager.get_parameter_display(param)} "
                    f"({config[param]}mm) below minimum tolerance ({self.tolerance}mm)"
                )
                self.affected_params.add(param)
    
    def _generate_fix_suggestions(self, config: Dict) -> List[str]:
        """Generate comprehensive fix suggestions for all error types"""
        suggestions = []

        # Create suggestion for every error type
        error_suggestion_map = {
            'below minimum': self._suggest_increase_parameter,
            'above maximum': self._suggest_decrease_parameter,
            'too wide for polygon': self._suggest_slot_polygon_fix,
            'intersecting': self._suggest_clearance_fix,
            'interference': self._suggest_interference_fix,
            'too small': self._suggest_size_increase,
            'below minimum tolerance': self._suggest_tolerance_fix
        }

        # Analyze each error and generate specific suggestion
        for error in self.critical_errors:
            suggestion_generated = False

            # Check for specific error patterns
            for pattern, suggestion_func in error_suggestion_map.items():
                if pattern in error.lower():
                    suggestion = suggestion_func(error, config)
                    if suggestion:
                        suggestions.append(suggestion)
                        suggestion_generated = True
                        break

            # Fallback for any error without specific suggestion
            if not suggestion_generated:
                suggestions.append(f"For '{error[:50]}...' - try adjusting the highlighted parameters")

        # Analyze error patterns and provide specific fixes
        if 'slotWidth' in self.affected_params and 'concentricPolygonRadius' in self.affected_params:
            numSides = config.get('numSides', 6)
            current_slot = config.get('slotWidth', 26)
            current_radius = config.get('concentricPolygonRadius', 30)

            # Calculate safe values with tolerance and safety margin
            theoretical_slot = 2 * current_radius * np.tan(np.pi / numSides) - 2 * self.tolerance
            theoretical_radius = (current_slot + 2 * self.tolerance) / (2 * np.tan(np.pi / numSides))

            safe_slot = self._calculate_safe_value(theoretical_slot, 'dimension')
            safe_radius = self._calculate_safe_value(theoretical_radius, 'dimension')

            suggestions.append(
                f"Quick fix options:\n"
                f"  1. Set {ConfigurationManager.get_parameter_display('slotWidth')} → {safe_slot:.2f}mm\n"
                f"  2. Set {ConfigurationManager.get_parameter_display('concentricPolygonRadius')} → {safe_radius:.2f}mm"
            )

        if 'tactorRadius' in self.affected_params and 'magnetRingRadius' in self.affected_params:
            magnetRadius = config.get('magnetRadius', 5)
            magnetRingRadius = config.get('magnetRingRadius', 20)
            numSides = config.get('numSides', 6)

            theoretical_tactor = (magnetRingRadius - magnetRadius - self.tolerance) * np.cos(np.pi / numSides) if numSides > 2 else magnetRingRadius - magnetRadius - self.tolerance
            theoretical_ring = config.get('tactorRadius', 10) + magnetRadius + self.tolerance

            safe_tactor = self._calculate_safe_value(theoretical_tactor, 'dimension')
            safe_ring = self._calculate_safe_value(theoretical_ring, 'dimension')

            suggestions.append(
                f"Tactor-magnet clearance fix:\n"
                f"  1. Set {ConfigurationManager.get_parameter_display('tactorRadius')} → {safe_tactor:.2f}mm\n"
                f"  2. Set {ConfigurationManager.get_parameter_display('magnetRingRadius')} → {safe_ring:.2f}mm"
            )

        return suggestions

    def _suggest_increase_parameter(self, error: str, config: Dict) -> str:
        """Suggest increasing a parameter that's below minimum"""
        import re
        param_match = re.search(r'\[(\d+)\] ([^:]+)', error)
        if param_match:
            param_name = param_match.group(2).strip()
            # Find the actual parameter name from display name
            for name, param_def in ConfigurationManager.PARAMETERS.items():
                if param_def.display_name == param_name:
                    safe_value = PrecisionHandler.round_value(param_def.min_value + 0.5)
                    unit_symbol = "°" if param_def.unit == "degrees" else param_def.unit
                    return f"Set {ConfigurationManager.get_parameter_display(name)} → {safe_value:.2f}{unit_symbol}"
        return None

    def _suggest_decrease_parameter(self, error: str, config: Dict) -> str:
        """Suggest decreasing a parameter that's above maximum"""
        import re
        param_match = re.search(r'\[(\d+)\] ([^:]+)', error)
        if param_match:
            param_name = param_match.group(2).strip()
            # Find the actual parameter name from display name
            for name, param_def in ConfigurationManager.PARAMETERS.items():
                if param_def.display_name == param_name:
                    safe_value = PrecisionHandler.round_value(param_def.max_value - 0.5)
                    unit_symbol = "°" if param_def.unit == "degrees" else param_def.unit
                    return f"Set {ConfigurationManager.get_parameter_display(name)} → {safe_value:.2f}{unit_symbol}"
        return None

    def _suggest_slot_polygon_fix(self, error: str, config: Dict) -> str:
        """Suggest fixes for slot width vs polygon size issues"""
        return "Adjust slot width or polygon radius to maintain proper clearances"

    def _suggest_clearance_fix(self, error: str, config: Dict) -> str:
        """Suggest fixes for clearance/intersection issues"""
        return "Increase clearances between components or reduce component sizes"

    def _suggest_interference_fix(self, error: str, config: Dict) -> str:
        """Suggest fixes for component interference"""
        return "Adjust component positions or sizes to eliminate interference"

    def _suggest_size_increase(self, error: str, config: Dict) -> str:
        """Suggest increasing size for components that are too small"""
        import re
        value_match = re.search(r'(\d+\.?\d*)', error)
        if value_match:
            current_value = float(value_match.group(1))
            suggested_value = current_value * 1.2  # 20% increase
            return f"Increase the parameter to at least {suggested_value:.1f}mm"
        return "Increase the parameter value"

    def _suggest_tolerance_fix(self, error: str, config: Dict) -> str:
        """Suggest fixes for tolerance violations"""
        return f"Increase clearance to at least {self.tolerance * 1.2:.1f}mm for reliable manufacturing"

    def _calculate_safe_value(self, theoretical_value: float, param_type: str) -> float:
        """Add safety margin to prevent edge case failures"""
        SAFETY_MARGINS = {
            'clearance': 1.2,    # 20% margin for clearances
            'dimension': 1.1,     # 10% margin for dimensions
            'angle': 1.05,        # 5% margin for angles
            'count': 1.0          # No margin for counts
        }

        margin = SAFETY_MARGINS.get(param_type, 1.1)
        safe_value = theoretical_value * margin

        # Round appropriately
        if param_type == 'count':
            return int(safe_value)
        elif param_type == 'angle':
            return round(safe_value, 0)  # Round to nearest degree
        else:
            return round(safe_value, 1)  # Round to 0.1mm
