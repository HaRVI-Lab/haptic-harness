"""
Haptic Harness Generator - A software to easily generate parameterized tiles for haptic harnesses.

This package provides:
- Core generation functionality through the Generator class
- Configuration management through ConfigurationManager
- User interface through MainWindow
- Validation through ValidationEngine

Example usage:
    from haptic_harness_generator import Generator
    generator = Generator('/path/to/output')
    generator.regen()
"""

from .main import run_app
from .core.generator import Generator
from .core.config_manager import ConfigurationManager
from .core.validation_engine import ValidationEngine
from .ui.main_window import MyMainWindow as MainWindow

__version__ = "0.0.42"
__all__ = ['run_app', 'Generator', 'ConfigurationManager', 'ValidationEngine', 'MainWindow']

if __name__ == "__main__":
    run_app()
