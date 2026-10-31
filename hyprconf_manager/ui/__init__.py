"""
UI package for Hyprland Config Manager.
"""

from .app import HyprlandConfigApp, MainWindow
from .style import apply_custom_css

__all__ = ["HyprlandConfigApp", "MainWindow", "apply_custom_css"]
