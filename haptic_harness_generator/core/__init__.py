"""
Core functionality for the Haptic Harness Generator.

This module contains the core business logic including:
- Generator: Main generation engine
- ConfigurationManager: Configuration handling
- ValidationEngine: Parameter validation
"""

from .generator import Generator
from .config_manager import ConfigurationManager
from .validation_engine import ValidationEngine

__all__ = ['Generator', 'ConfigurationManager', 'ValidationEngine']
