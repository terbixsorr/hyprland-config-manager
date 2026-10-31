"""
Core logic for Hyprland Config Manager.
AST parser, models, engine, backups, validation, safe apply, and hyprctl integration.
"""

from .ast_nodes import ASTNode, ConfigFileAST
from .parser import HyprlandParser
from .generator import HyprlandGenerator
from .models import (
    MonitorConfig,
    WindowsConfig,
    AnimationsConfig,
    AppearanceConfig,
    KeybindItem,
    InputConfig,
    StartupItem,
    WorkspaceRule,
    WindowRuleItem,
    WallpaperConfig,
    EnvironmentConfig,
    APPEARANCE_THEMES,
    ANIMATION_PRESETS,
)
from .config_engine import HyprlandConfigEngine
from .hyprctl import HyprctlClient, HyprlandStatus
from .backup_manager import BackupManager, BackupEntry
from .validator import HyprlandValidator, ValidationResult, ValidationError, ValidationWarning
from .profile_manager import ProfileManager
from .safe_apply import SafeApplyPipeline, ApplyResult

__all__ = [
    "ASTNode",
    "ConfigFileAST",
    "HyprlandParser",
    "HyprlandGenerator",
    "MonitorConfig",
    "WindowsConfig",
    "AnimationsConfig",
    "AppearanceConfig",
    "KeybindItem",
    "InputConfig",
    "StartupItem",
    "WorkspaceRule",
    "WindowRuleItem",
    "WallpaperConfig",
    "EnvironmentConfig",
    "APPEARANCE_THEMES",
    "ANIMATION_PRESETS",
    "HyprlandConfigEngine",
    "HyprctlClient",
    "HyprlandStatus",
    "BackupManager",
    "BackupEntry",
    "HyprlandValidator",
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "ProfileManager",
    "SafeApplyPipeline",
    "ApplyResult",
]
