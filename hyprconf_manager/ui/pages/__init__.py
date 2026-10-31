"""
UI pages for Hyprland Config Manager.
"""

from .dashboard_page import DashboardPageBuilder
from .monitors_page import MonitorsPageBuilder
from .windows_page import WindowsPageBuilder
from .appearance_page import AppearancePageBuilder
from .animations_page import AnimationsPageBuilder
from .input_page import InputPageBuilder
from .keybinds_page import KeybindsPageBuilder
from .startup_page import StartupPageBuilder
from .workspaces_page import WorkspacesPageBuilder
from .rules_page import RulesPageBuilder
from .wallpapers_page import WallpapersPageBuilder
from .environment_page import EnvironmentPageBuilder
from .advanced_page import AdvancedPageBuilder
from .profiles_page import ProfilesPageBuilder
from .config_editor_page import ConfigEditorPageBuilder
from .backups_page import BackupsPageBuilder

__all__ = [
    "DashboardPageBuilder",
    "MonitorsPageBuilder",
    "WindowsPageBuilder",
    "AppearancePageBuilder",
    "AnimationsPageBuilder",
    "InputPageBuilder",
    "KeybindsPageBuilder",
    "StartupPageBuilder",
    "WorkspacesPageBuilder",
    "RulesPageBuilder",
    "WallpapersPageBuilder",
    "EnvironmentPageBuilder",
    "AdvancedPageBuilder",
    "ProfilesPageBuilder",
    "ConfigEditorPageBuilder",
    "BackupsPageBuilder",
]
