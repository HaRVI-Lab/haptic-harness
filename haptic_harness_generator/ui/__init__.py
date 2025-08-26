"""
User interface components for the Haptic Harness Generator.

This module contains all UI-related functionality including:
- MainWindow: Primary application window
- UI helper classes: ParameterWidget, ValidationDisplay, etc.
- Styles: Application styling and themes
"""

from .main_window import MyMainWindow as MainWindow
from .ui_helpers import (ParameterWidget, ValidationDisplay, ScalingHelper,
                        PresetSelector, ParameterCategory)
from .styles import Styles

__all__ = ['MainWindow', 'ParameterWidget', 'ValidationDisplay', 'ScalingHelper',
           'PresetSelector', 'ParameterCategory', 'Styles']
