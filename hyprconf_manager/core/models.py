"""
Data models for Hyprland configuration.
Typed representations of all configurable components with preset definitions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class MonitorConfig:
    name: str = ""  # empty string means default wildcard monitor
    resolution: str = "1920x1080"
    refresh_rate: float = 60.0
    position: str = "0x0"
    scale: float = 1.0
    vrr: int = 0  # 0 = off, 1 = on, 2 = fullscreen
    enabled: bool = True
    is_primary: bool = False
    transform: int = 0  # 0: normal, 1: 90, 2: 180, 3: 270...

    def to_directive_value(self) -> str:
        if not self.enabled:
            return f"{self.name},disable" if self.name else ",disable"
        
        mode = f"{self.resolution}@{self.refresh_rate:g}" if self.refresh_rate else self.resolution
        val = f"{self.name},{mode},{self.position},{self.scale:g}"
        extras = []
        if self.vrr:
            extras.append(f"vrr,{self.vrr}")
        if self.transform:
            extras.append(f"transform,{self.transform}")
        if extras:
            val += f",{','.join(extras)}"
        return val


@dataclass
class WindowsConfig:
    border_size: int = 2
    rounding: int = 8
    gaps_in: int = 5
    gaps_out: int = 15
    layout: str = "dwindle"
    active_opacity: float = 1.0
    inactive_opacity: float = 0.85
    fullscreen_opacity: float = 1.0
    drop_shadow: bool = True
    shadow_range: int = 12
    shadow_render_power: int = 3
    shadow_color: str = "rgba(1a1a1aee)"
    blur_enabled: bool = True
    blur_size: int = 6
    blur_passes: int = 2
    blur_new_optimizations: bool = True
    follow_mouse: int = 1
    float_switch_override_focus: int = 2


@dataclass
class AnimationsConfig:
    enabled: bool = True
    speed_multiplier: float = 1.0
    bezier_curves: Dict[str, str] = field(default_factory=lambda: {
        "myBezier": "0.05, 0.9, 0.1, 1.05",
        "smoothOut": "0.36, 0, 0.66, -0.56",
        "smoothIn": "0.25, 1, 0.5, 1",
        "linear": "0, 0, 1, 1",
    })
    # target -> (enabled, speed, curve, [style])
    animations: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "windows": {"enabled": True, "speed": 6, "curve": "myBezier", "style": "slide"},
        "windowsOut": {"enabled": True, "speed": 6, "curve": "default", "style": "popin 80%"},
        "border": {"enabled": True, "speed": 8, "curve": "default", "style": ""},
        "borderangle": {"enabled": True, "speed": 8, "curve": "default", "style": ""},
        "fade": {"enabled": True, "speed": 6, "curve": "default", "style": ""},
        "workspaces": {"enabled": True, "speed": 5, "curve": "myBezier", "style": "slide"},
    })
    preset: str = "Smooth"


ANIMATION_PRESETS = {
    "Minimal": {
        "enabled": True,
        "bezier_curves": {"minimal": "0.1, 0.9, 0.2, 1.0"},
        "animations": {
            "windows": {"enabled": True, "speed": 2, "curve": "minimal", "style": "popin 90%"},
            "windowsOut": {"enabled": True, "speed": 2, "curve": "minimal", "style": "popin 90%"},
            "border": {"enabled": False, "speed": 1, "curve": "default", "style": ""},
            "fade": {"enabled": True, "speed": 2, "curve": "default", "style": ""},
            "workspaces": {"enabled": True, "speed": 2, "curve": "minimal", "style": "slide"},
        }
    },
    "Smooth": {
        "enabled": True,
        "bezier_curves": {
            "smooth": "0.25, 1, 0.5, 1",
            "overshot": "0.05, 0.9, 0.1, 1.05",
        },
        "animations": {
            "windows": {"enabled": True, "speed": 7, "curve": "overshot", "style": "popin 85%"},
            "windowsOut": {"enabled": True, "speed": 6, "curve": "smooth", "style": "popin 80%"},
            "border": {"enabled": True, "speed": 10, "curve": "default", "style": ""},
            "fade": {"enabled": True, "speed": 7, "curve": "default", "style": ""},
            "workspaces": {"enabled": True, "speed": 6, "curve": "smooth", "style": "slide"},
        }
    },
    "Fast": {
        "enabled": True,
        "bezier_curves": {"fast": "0.0, 0.0, 0.2, 1.0"},
        "animations": {
            "windows": {"enabled": True, "speed": 3, "curve": "fast", "style": "popin 80%"},
            "windowsOut": {"enabled": True, "speed": 3, "curve": "fast", "style": "popin 80%"},
            "border": {"enabled": True, "speed": 4, "curve": "default", "style": ""},
            "fade": {"enabled": True, "speed": 3, "curve": "default", "style": ""},
            "workspaces": {"enabled": True, "speed": 3, "curve": "fast", "style": "slide"},
        }
    },
    "Gaming": {
        "enabled": False,
        "bezier_curves": {"linear": "0, 0, 1, 1"},
        "animations": {
            "windows": {"enabled": False, "speed": 1, "curve": "linear", "style": ""},
            "windowsOut": {"enabled": False, "speed": 1, "curve": "linear", "style": ""},
            "border": {"enabled": False, "speed": 1, "curve": "linear", "style": ""},
            "fade": {"enabled": False, "speed": 1, "curve": "linear", "style": ""},
            "workspaces": {"enabled": False, "speed": 1, "curve": "linear", "style": ""},
        }
    }
}


@dataclass
class AppearanceConfig:
    theme_name: str = "Catppuccin"
    col_active_border: str = "rgba(33ccffee) rgba(00ff99ee) 45deg"
    col_inactive_border: str = "rgba(595959aa)"
    rounding: int = 10
    shadow_enabled: bool = True
    blur_enabled: bool = True
    transparency: float = 0.95


APPEARANCE_THEMES = {
    "Catppuccin": {
        "col_active_border": "rgba(ca9ee6ee) rgba(8caaeeee) 45deg",
        "col_inactive_border": "rgba(414559aa)",
        "rounding": 10,
        "shadow_color": "rgba(181926aa)",
        "accent": "#ca9ee6",
        "background": "#24273a",
    },
    "Tokyo Night": {
        "col_active_border": "rgba(7aa2f7ee) rgba(bb9af7ee) 45deg",
        "col_inactive_border": "rgba(24283baa)",
        "rounding": 10,
        "shadow_color": "rgba(16161eaa)",
        "accent": "#7aa2f7",
        "background": "#1a1b26",
    },
    "Gruvbox": {
        "col_active_border": "rgba(d79921ee) rgba(fabd2fee) 45deg",
        "col_inactive_border": "rgba(504945aa)",
        "rounding": 6,
        "shadow_color": "rgba(282828aa)",
        "accent": "#d79921",
        "background": "#282828",
    },
    "Nord": {
        "col_active_border": "rgba(88c0d0ee) rgba(81a1c1ee) 45deg",
        "col_inactive_border": "rgba(434c5eaa)",
        "rounding": 8,
        "shadow_color": "rgba(2e3440aa)",
        "accent": "#88c0d0",
        "background": "#2e3440",
    },
    "Dracula": {
        "col_active_border": "rgba(bd93f9ee) rgba(ff79c6ee) 45deg",
        "col_inactive_border": "rgba(44475aaa)",
        "rounding": 10,
        "shadow_color": "rgba(282a36aa)",
        "accent": "#bd93f9",
        "background": "#282a36",
    },
    "AMOLED": {
        "col_active_border": "rgba(00f0ffee) rgba(00ff66ee) 45deg",
        "col_inactive_border": "rgba(181818ff)",
        "rounding": 12,
        "shadow_color": "rgba(00000000)",
        "accent": "#00f0ff",
        "background": "#000000",
    },
    "Dark": {
        "col_active_border": "rgba(3b82f6ee) rgba(6366f1ee) 45deg",
        "col_inactive_border": "rgba(334155aa)",
        "rounding": 8,
        "shadow_color": "rgba(090d16cc)",
        "accent": "#3b82f6",
        "background": "#0f172a",
    },
    "Light": {
        "col_active_border": "rgba(0284c7ee) rgba(2563ebee) 45deg",
        "col_inactive_border": "rgba(cbd5e1cc)",
        "rounding": 8,
        "shadow_color": "rgba(00000015)",
        "accent": "#0284c7",
        "background": "#f8fafc",
    },
}


@dataclass
class KeybindItem:
    modifier: str = "SUPER"
    key: str = "Q"
    dispatcher: str = "exec"
    arguments: str = "kitty"
    flag: str = ""  # "" = bind, "m" = bindm, "l" = bindl, "e" = binde, "r" = bindr
    comment: str = ""

    def get_full_combination(self) -> str:
        mods = self.modifier.strip().replace(" ", "")
        k = self.key.strip()
        if mods and k:
            return f"{mods} + {k}"
        elif k:
            return k
        return mods or "Unbound"

    def to_directive(self) -> str:
        prefix = f"bind{self.flag}" if self.flag else "bind"
        val = f"{self.modifier}, {self.key}, {self.dispatcher}"
        if self.arguments:
            val += f", {self.arguments}"
        return f"{prefix} = {val}"


@dataclass
class InputConfig:
    mouse_sensitivity: float = 0.0
    accel_profile: str = "adaptive"  # adaptive, flat
    natural_scroll: bool = False
    kb_layout: str = "us,ru"
    kb_variant: str = ""
    kb_options: str = "grp:alt_shift_toggle,caps:escape"
    repeat_rate: int = 50
    repeat_delay: int = 300
    numlock_by_default: bool = True
    touchpad_natural_scroll: bool = True
    touchpad_tap_to_click: bool = True
    touchpad_drag_lock: bool = False
    touchpad_disable_while_typing: bool = True

    @property
    def sensitivity(self) -> float:
        return self.mouse_sensitivity

    @sensitivity.setter
    def sensitivity(self, val: float):
        self.mouse_sensitivity = float(val)


@dataclass
class StartupItem:
    command: str = "waybar"
    exec_type: str = "exec-once"  # exec-once or exec
    enabled: bool = True
    comment: str = ""

    def to_directive(self) -> str:
        prefix = self.exec_type
        if self.enabled:
            return f"{prefix} = {self.command}"
        return f"# {prefix} = {self.command}"


@dataclass
class WorkspaceRule:
    workspace_id: str = "1"
    monitor: str = ""
    default: bool = False
    persistent: bool = False
    gaps_in: Optional[int] = None
    gaps_out: Optional[int] = None

    def to_directive(self) -> str:
        parts = [self.workspace_id]
        if self.monitor:
            parts.append(f"monitor:{self.monitor}")
        if self.default:
            parts.append("default:true")
        if self.persistent:
            parts.append("persistent:true")
        if self.gaps_in is not None:
            parts.append(f"gapsin:{self.gaps_in}")
        if self.gaps_out is not None:
            parts.append(f"gapsout:{self.gaps_out}")
        return f"workspace = {','.join(parts)}"


@dataclass
class WindowRuleItem:
    app_class: str = ""
    app_title: str = ""
    workspace: Optional[str] = None
    floating: Optional[bool] = None
    fullscreen: Optional[bool] = None
    opacity: Optional[float] = None
    size: Optional[str] = None
    position: Optional[str] = None
    raw_rule: str = ""

    def to_directive(self) -> str:
        # If no structured properties are set and raw_rule is available, preserve raw
        has_structured = any([
            self.app_class,
            self.app_title,
            self.workspace,
            self.floating is not None,
            self.fullscreen is not None,
            self.opacity is not None,
            self.size,
            self.position,
        ])
        if not has_structured and self.raw_rule:
            return self.raw_rule

        # windowrulev2 = action, filters
        actions = []
        if self.floating is True:
            actions.append("float")
        elif self.floating is False:
            actions.append("tile")
        if self.fullscreen:
            actions.append("fullscreen")
        if self.opacity is not None:
            actions.append(f"opacity {self.opacity:g} override")
        if self.workspace:
            actions.append(f"workspace {self.workspace}")
        if self.size:
            actions.append(f"size {self.size}")
        if self.position:
            actions.append(f"move {self.position}")

        filters = []
        if self.app_class:
            filters.append(f"class:^({self.app_class})$")
        if self.app_title:
            filters.append(f"title:^({self.app_title})$")

        if not actions:
            actions.append("float")

        action_str = " ".join(actions) if len(actions) > 1 else actions[0]
        filter_str = f",{','.join(filters)}" if filters else ""
        return f"windowrulev2 = {action_str}{filter_str}"


@dataclass
class WallpaperConfig:
    daemon: str = "hyprpaper"  # hyprpaper, swww, swaybg, mpvpaper, feh
    current_path: str = ""
    monitor_wallpapers: Dict[str, str] = field(default_factory=dict)


@dataclass
class EnvironmentConfig:
    vars: Dict[str, str] = field(default_factory=lambda: {
        "XCURSOR_SIZE": "24",
        "QT_QPA_PLATFORM": "wayland",
        "GDK_BACKEND": "wayland,x11",
        "ELECTRON_OZONE_PLATFORM_HINT": "wayland",
    })
