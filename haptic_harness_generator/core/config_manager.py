"""
Configuration management module - handles all presets, validation rules, and parameter definitions
"""
import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from datetime import datetime

@dataclass
class ParameterDefinition:
    """Definition for a single parameter"""
    name: str
    display_name: str
    ui_number: int
    unit: str
    min_value: float
    max_value: float
    default_value: float
    tooltip: str
    category: str
    validation_dependencies: List[str] = None

class ConfigurationManager:
    """Central configuration management"""
    
    # PARAMETER DEFINITIONS - Single source of truth
    PARAMETERS = {
        "concentricPolygonRadius": ParameterDefinition(
            name="concentricPolygonRadius",
            display_name="Concentric Polygon Radius",
            ui_number=1,
            unit="mm",
            min_value=20,
            max_value=50,
            default_value=30,
            tooltip="Outer radius of the polygon tile. Determines overall size.",
            category="Tile Parameters",
            validation_dependencies=["tactorRadius", "magnetRingRadius", "slotWidth"]
        ),
        "tactorRadius": ParameterDefinition(
            name="tactorRadius",
            display_name="Tactor Radius",
            ui_number=2,
            unit="mm",
            min_value=5,
            max_value=20,
            default_value=10,
            tooltip="Radius of the tactor cavity. Must be smaller than (magnetRingRadius - magnetRadius - 2mm)",
            category="Tile Parameters",
            validation_dependencies=["magnetRingRadius", "magnetRadius"]
        ),
        "magnetRingRadius": ParameterDefinition(
            name="magnetRingRadius",
            display_name="Magnet Ring Radius",
            ui_number=3,
            unit="mm",
            min_value=15,
            max_value=35,
            default_value=20,
            tooltip="Distance from center to magnet positions",
            category="Tile Parameters",
            validation_dependencies=["tactorRadius", "magnetRadius", "concentricPolygonRadius"]
        ),
        "numSides": ParameterDefinition(
            name="numSides",
            display_name="Number of Sides",
            ui_number=0,
            unit="",
            min_value=3,
            max_value=8,
            default_value=6,
            tooltip="Polygon sides (3-8). 4 or 6 recommended for wrist mounting.",
            category="Tile Parameters",
            validation_dependencies=["concentricPolygonRadius", "slotWidth"]
        ),
        "foamThickness": ParameterDefinition(
            name="foamThickness",
            display_name="Foam Thickness",
            ui_number=0,
            unit="mm",
            min_value=0.5,
            max_value=5,
            default_value=1,
            tooltip="Thickness of foam layer between tactor and skin",
            category="Tile Parameters",
            validation_dependencies=[]
        ),
        "distanceBetweenMagnetClipAndPolygonEdge": ParameterDefinition(
            name="distanceBetweenMagnetClipAndPolygonEdge",
            display_name="Distance Between Magnet Clip And Polygon Edge",
            ui_number=4,
            unit="mm",
            min_value=1,
            max_value=10,
            default_value=3,
            tooltip="Distance from magnet clip to polygon edge",
            category="Tile Parameters",
            validation_dependencies=["concentricPolygonRadius", "magnetRadius"]
        ),
        "numMagnetsInRing": ParameterDefinition(
            name="numMagnetsInRing",
            display_name="Number of Magnets in Ring",
            ui_number=0,
            unit="",
            min_value=3,
            max_value=25,
            default_value=6,
            tooltip="Number of magnets arranged in a ring",
            category="Tile Parameters",
            validation_dependencies=["magnetRingRadius", "magnetRadius"]
        ),
        "magnetRadius": ParameterDefinition(
            name="magnetRadius",
            display_name="Magnet Radius",
            ui_number=5,
            unit="mm",
            min_value=1,
            max_value=10,
            default_value=5,
            tooltip="Radius of individual magnets",
            category="Magnet Parameters",
            validation_dependencies=["magnetRingRadius", "tactorRadius"]
        ),
        "magnetThickness": ParameterDefinition(
            name="magnetThickness",
            display_name="Magnet Thickness",
            ui_number=6,
            unit="mm",
            min_value=0.5,
            max_value=5,
            default_value=1,
            tooltip="Thickness of individual magnets",
            category="Magnet Parameters",
            validation_dependencies=[]
        ),
        "slotWidth": ParameterDefinition(
            name="slotWidth",
            display_name="Slot Width",
            ui_number=7,
            unit="mm",
            min_value=10,
            max_value=40,
            default_value=30,
            tooltip="Width of the slot in the clip",
            category="Clip Parameters",
            validation_dependencies=["concentricPolygonRadius", "numSides", "slotBorderRadius"]
        ),
        "slotHeight": ParameterDefinition(
            name="slotHeight",
            display_name="Slot Height",
            ui_number=8,
            unit="mm",
            min_value=0.5,
            max_value=5,
            default_value=1.5,
            tooltip="Height of the slot in the clip",
            category="Clip Parameters",
            validation_dependencies=[]
        ),
        "slotBorderRadius": ParameterDefinition(
            name="slotBorderRadius",
            display_name="Slot Border Radius",
            ui_number=9,
            unit="mm",
            min_value=5,
            max_value=25,
            default_value=10,
            tooltip="Radius of the slot border for rounded corners",
            category="Clip Parameters",
            validation_dependencies=["slotWidth", "concentricPolygonRadius"]
        ),
        "magnetClipThickness": ParameterDefinition(
            name="magnetClipThickness",
            display_name="Magnet Clip Thickness",
            ui_number=10,
            unit="mm",
            min_value=0.5,
            max_value=5,
            default_value=1.5,
            tooltip="Thickness of the magnet clip walls",
            category="Clip Parameters",
            validation_dependencies=[]
        ),
        "magnetClipRingThickness": ParameterDefinition(
            name="magnetClipRingThickness",
            display_name="Magnet Clip Ring Thickness",
            ui_number=11,
            unit="mm",
            min_value=0.5,
            max_value=5,
            default_value=1.5,
            tooltip="Thickness of the magnet clip ring",
            category="Clip Parameters",
            validation_dependencies=[]
        ),
        "distanceBetweenMagnetsInClip": ParameterDefinition(
            name="distanceBetweenMagnetsInClip",
            display_name="Distance Between Magnets In Clip",
            ui_number=12,
            unit="mm",
            min_value=5,
            max_value=30,
            default_value=15,
            tooltip="Distance between magnets in the clip",
            category="Clip Parameters",
            validation_dependencies=["magnetRadius"]
        ),
        "distanceBetweenMagnetClipAndSlot": ParameterDefinition(
            name="distanceBetweenMagnetClipAndSlot",
            display_name="Distance Between Magnet Clip And Slot",
            ui_number=13,
            unit="mm",
            min_value=1,
            max_value=10,
            default_value=3,
            tooltip="Distance between magnet clip and slot",
            category="Clip Parameters",
            validation_dependencies=[]
        ),
        "mountRadius": ParameterDefinition(
            name="mountRadius",
            display_name="Mount Radius",
            ui_number=14,
            unit="mm",
            min_value=5,
            max_value=20,
            default_value=13,
            tooltip="Radius of the mount component",
            category="Mount Parameters",
            validation_dependencies=["magnetRingRadius", "magnetRadius"]
        ),
        "mountHeight": ParameterDefinition(
            name="mountHeight",
            display_name="Mount Height",
            ui_number=15,
            unit="mm",
            min_value=5,
            max_value=20,
            default_value=10,
            tooltip="Height of the mount component",
            category="Mount Parameters",
            validation_dependencies=[]
        ),
        "mountShellThickness": ParameterDefinition(
            name="mountShellThickness",
            display_name="Mount Shell Thickness",
            ui_number=16,
            unit="mm",
            min_value=1,
            max_value=5,
            default_value=2,
            tooltip="Thickness of the mount shell walls",
            category="Mount Parameters",
            validation_dependencies=[]
        ),
        "mountBottomAngleOpening": ParameterDefinition(
            name="mountBottomAngleOpening",
            display_name="Mount Bottom Angle Opening",
            ui_number=17,
            unit="degrees",
            min_value=30,
            max_value=180,
            default_value=60,
            tooltip="Bottom angle opening of the mount in degrees",
            category="Mount Parameters",
            validation_dependencies=[]
        ),
        "mountTopAngleOpening": ParameterDefinition(
            name="mountTopAngleOpening",
            display_name="Mount Top Angle Opening",
            ui_number=18,
            unit="degrees",
            min_value=30,
            max_value=180,
            default_value=45,
            tooltip="Top angle opening of the mount in degrees",
            category="Mount Parameters",
            validation_dependencies=[]
        ),
        "brim": ParameterDefinition(
            name="brim",
            display_name="Brim",
            ui_number=19,
            unit="mm",
            min_value=1,
            max_value=10,
            default_value=3,
            tooltip="Brim size for 3D printing support",
            category="Mount Parameters",
            validation_dependencies=[]
        ),
        "strapWidth": ParameterDefinition(
            name="strapWidth",
            display_name="Strap Width",
            ui_number=20,
            unit="mm",
            min_value=5,
            max_value=40,
            default_value=10,
            tooltip="Width of the strap",
            category="Strap Parameters",
            validation_dependencies=[]
        ),
        "strapThickness": ParameterDefinition(
            name="strapThickness",
            display_name="Strap Thickness",
            ui_number=21,
            unit="mm",
            min_value=0.5,
            max_value=5,
            default_value=1,
            tooltip="Thickness of the strap",
            category="Strap Parameters",
            validation_dependencies=[]
        ),
        "strapClipThickness": ParameterDefinition(
            name="strapClipThickness",
            display_name="Strap Clip Thickness",
            ui_number=22,
            unit="mm",
            min_value=0.5,
            max_value=5,
            default_value=1,
            tooltip="Thickness of the strap clip",
            category="Strap Parameters",
            validation_dependencies=[]
        ),
        "strapClipRadius": ParameterDefinition(
            name="strapClipRadius",
            display_name="Strap Clip Radius",
            ui_number=23,
            unit="mm",
            min_value=0.5,
            max_value=5,
            default_value=1,
            tooltip="Radius of the strap clip",
            category="Strap Parameters",
            validation_dependencies=["strapClipRim"]
        ),
        "distanceBetweenStrapsInClip": ParameterDefinition(
            name="distanceBetweenStrapsInClip",
            display_name="Distance Between Straps In Clip",
            ui_number=24,
            unit="mm",
            min_value=1,
            max_value=10,
            default_value=2,
            tooltip="Distance between straps in the clip",
            category="Strap Parameters",
            validation_dependencies=[]
        ),
        "strapClipRim": ParameterDefinition(
            name="strapClipRim",
            display_name="Strap Clip Rim",
            ui_number=25,
            unit="mm",
            min_value=1,
            max_value=10,
            default_value=2,
            tooltip="Rim size of the strap clip",
            category="Strap Parameters",
            validation_dependencies=["strapClipRadius"]
        ),
    }

    # VALIDATED PRESET CONFIGURATIONS
    PRESETS = {
        "Standard 4-sided": {
            "concentricPolygonRadius": 32,
            "tactorRadius": 12.7,
            "magnetRingRadius": 22,
            "numSides": 4,
            "foamThickness": 2,
            "distanceBetweenMagnetClipAndPolygonEdge": 4,
            "numMagnetsInRing": 6,
            "magnetRadius": 2.5,
            "magnetThickness": 1.8,
            "slotWidth": 25,  # Reduced for safety
            "slotHeight": 1.5,
            "slotBorderRadius": 8,  # Reduced for safety
            "magnetClipThickness": 1.5,
            "magnetClipRingThickness": 1.5,
            "distanceBetweenMagnetsInClip": 15,
            "distanceBetweenMagnetClipAndSlot": 4,
            "mountRadius": 12,
            "mountHeight": 10,
            "mountShellThickness": 2,
            "mountBottomAngleOpening": 60,
            "mountTopAngleOpening": 45,
            "brim": 3,
            "strapWidth": 25,
            "strapThickness": 2,
            "strapClipThickness": 1.5,
            "strapClipRadius": 1,
            "distanceBetweenStrapsInClip": 2,
            "strapClipRim": 2
        },
        "Compact 4-sided": {
            "concentricPolygonRadius": 28,
            "tactorRadius": 10,
            "magnetRingRadius": 20,
            "numSides": 4,
            "foamThickness": 2,
            "distanceBetweenMagnetClipAndPolygonEdge": 3,
            "numMagnetsInRing": 6,
            "magnetRadius": 2.5,
            "magnetThickness": 1.8,
            "slotWidth": 22,  # Adjusted for compact design
            "slotHeight": 1.5,
            "slotBorderRadius": 7,  # Adjusted for compact design
            "magnetClipThickness": 1.5,
            "magnetClipRingThickness": 1.5,
            "distanceBetweenMagnetsInClip": 15,
            "distanceBetweenMagnetClipAndSlot": 3,
            "mountRadius": 11,
            "mountHeight": 10,
            "mountShellThickness": 2,
            "mountBottomAngleOpening": 60,
            "mountTopAngleOpening": 45,
            "brim": 3,
            "strapWidth": 22,
            "strapThickness": 2,
            "strapClipThickness": 1.5,
            "strapClipRadius": 1,
            "distanceBetweenStrapsInClip": 2,
            "strapClipRim": 2
        },
        "Standard 6-sided": {
            # Use exact values from working configuration
            "concentricPolygonRadius": 30,
            "tactorRadius": 10,
            "magnetRingRadius": 20,
            "numSides": 6,
            "foamThickness": 1,
            "distanceBetweenMagnetClipAndPolygonEdge": 3,
            "numMagnetsInRing": 6,
            "magnetRadius": 5,
            "magnetThickness": 1,
            "slotWidth": 26,  # Adjusted for 6 sides
            "slotHeight": 1.5,
            "slotBorderRadius": 8,  # Safe value
            "magnetClipThickness": 1.5,
            "magnetClipRingThickness": 1.5,
            "distanceBetweenMagnetsInClip": 15,
            "distanceBetweenMagnetClipAndSlot": 3,
            "mountRadius": 12,
            "mountHeight": 10,
            "mountShellThickness": 2,
            "mountBottomAngleOpening": 60,
            "mountTopAngleOpening": 45,
            "brim": 3,
            "strapWidth": 10,
            "strapThickness": 1,
            "strapClipThickness": 1,
            "strapClipRadius": 1,
            "distanceBetweenStrapsInClip": 2,
            "strapClipRim": 2
        }
    }

    @classmethod
    def get_parameter_display(cls, param_name: str) -> str:
        """Get display name with UI number (improved formatting)"""
        param = cls.PARAMETERS.get(param_name)
        if param:
            if param.ui_number > 0:
                return f"[{param.ui_number}] {param.display_name}"
            else:
                return f"{param.display_name}"  # Remove bracket entirely for [0]
        return param_name

    @classmethod
    def validate_config(cls, config: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a configuration
        Returns: (is_valid, error_messages, affected_parameters)
        """
        errors = []
        affected_params = []

        # Check parameter ranges
        for param_name, param_def in cls.PARAMETERS.items():
            if param_name in config:
                value = config[param_name]
                if value < param_def.min_value or value > param_def.max_value:
                    errors.append(
                        f"{cls.get_parameter_display(param_name)}: "
                        f"Value {value} outside range [{param_def.min_value}, {param_def.max_value}]"
                    )
                    affected_params.append(param_name)

        # Geometry-specific validations
        errors_geo, params_geo = cls._validate_geometry(config)
        errors.extend(errors_geo)
        affected_params.extend(params_geo)

        return len(errors) == 0, errors, list(set(affected_params))

    @classmethod
    def _validate_geometry(cls, config: Dict) -> Tuple[List[str], List[str]]:
        """Validate geometric constraints"""
        errors = []
        params = []
        tolerance = 1.0

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

        # Critical validation 1: Polygon edge vs slot width
        polygon_edge = 2 * concentricPolygonRadius * np.tan(np.pi / numSides)
        if slotWidth + 2 * tolerance > polygon_edge:
            safe_slot_width = polygon_edge - 2 * tolerance
            safe_polygon_radius = (slotWidth + 2 * tolerance) / (2 * np.tan(np.pi / numSides))
            errors.append(
                f"Slot too wide for polygon:\n"
                f"  Current: {cls.get_parameter_display('slotWidth')} = {slotWidth:.1f}mm\n"
                f"  Polygon edge = {polygon_edge:.1f}mm\n"
                f"  Options:\n"
                f"    • Reduce {cls.get_parameter_display('slotWidth')} to < {safe_slot_width:.0f}mm\n"
                f"    • Increase {cls.get_parameter_display('concentricPolygonRadius')} to > {safe_polygon_radius:.0f}mm"
            )
            params.extend(['slotWidth', 'concentricPolygonRadius', 'numSides'])

        # Critical validation 2: Flap intersection check
        if polygon_edge > 0:
            x = (polygon_edge - slotWidth) / 2
            y = (distanceBetweenMagnetClipAndPolygonEdge +
                 2 * (magnetRadius + magnetClipRingThickness) +
                 distanceBetweenMagnetClipAndSlot + slotHeight / 2)

            if x > 0 and y > 0:
                beta = np.arctan(x / y)
                hypo = x / np.sin(beta)
                phi = (np.pi * (numSides - 2)) / numSides
                theta = (np.pi - phi) / 2
                dist = np.sin(beta + theta) * hypo

                if dist < slotBorderRadius + tolerance:
                    errors.append(
                        f"Flap edges intersecting:\n"
                        f"  Clearance = {dist:.1f}mm, Need > {slotBorderRadius + tolerance:.1f}mm\n"
                        f"  Options:\n"
                        f"    • Reduce {cls.get_parameter_display('slotWidth')} (current: {slotWidth}mm)\n"
                        f"    • Reduce {cls.get_parameter_display('slotBorderRadius')} (current: {slotBorderRadius}mm)\n"
                        f"    • Increase {cls.get_parameter_display('concentricPolygonRadius')} (current: {concentricPolygonRadius}mm)"
                    )
                    params.extend(['slotWidth', 'slotBorderRadius', 'concentricPolygonRadius'])

        # Critical validation 3: Tactor vs magnet clearance
        max_tactor_reach = tactorRadius if numSides == 2 else tactorRadius / np.cos(np.pi / numSides)
        if max_tactor_reach + tolerance > magnetRingRadius - magnetRadius:
            safe_tactor = (magnetRingRadius - magnetRadius - tolerance) * np.cos(np.pi / numSides)
            safe_ring = max_tactor_reach + magnetRadius + tolerance
            errors.append(
                f"Tactor-magnet interference:\n"
                f"  Options:\n"
                f"    • Reduce {cls.get_parameter_display('tactorRadius')} to < {safe_tactor:.1f}mm\n"
                f"    • Increase {cls.get_parameter_display('magnetRingRadius')} to > {safe_ring:.0f}mm"
            )
            params.extend(['tactorRadius', 'magnetRingRadius', 'magnetRadius'])

        return errors, params

    @classmethod
    def export_config(cls, config: Dict, filepath: str) -> bool:
        """Export configuration with metadata"""
        export_data = {
            "version": "3.0",
            "parameters": config,
            "metadata": {
                "created": str(datetime.now()),
                "validated": cls.validate_config(config)[0]
            }
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False

    @classmethod
    def import_config(cls, filepath: str) -> Optional[Dict]:
        """Import and validate configuration"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Handle different versions
            if "parameters" in data:
                config = data["parameters"]
            else:
                config = data  # Old format

            # Validate
            is_valid, errors, _ = cls.validate_config(config)
            if not is_valid:
                print(f"Warning: Imported config has validation errors:\n{errors}")

            return config
        except Exception as e:
            print(f"Import failed: {e}")
            return None
