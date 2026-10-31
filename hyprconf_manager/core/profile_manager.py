"""
Profile Manager for Hyprland Config Manager.
Allows saving, switching, exporting, importing, and activating named profiles
such as Gaming, Work, Laptop, Minimal, and Streaming.
"""

import json
import os
import shutil
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple


DEFAULT_PROFILES = {
    "Gaming": {
        "description": "Maximized performance: zero animations, VRR enabled, thin borders, zero blur",
        "windows": {
            "border_size": 1,
            "rounding": 0,
            "gaps_in": 0,
            "gaps_out": 0,
            "active_opacity": 1.0,
            "inactive_opacity": 1.0,
            "drop_shadow": False,
            "blur_enabled": False,
        },
        "animations": {
            "enabled": False,
            "preset": "Gaming"
        },
        "appearance": {
            "theme_name": "AMOLED"
        }
    },
    "Work": {
        "description": "Ergonomic productivity: balanced gaps, Catppuccin theme, smooth transitions",
        "windows": {
            "border_size": 2,
            "rounding": 10,
            "gaps_in": 6,
            "gaps_out": 14,
            "active_opacity": 1.0,
            "inactive_opacity": 0.9,
            "drop_shadow": True,
            "blur_enabled": True,
            "blur_size": 5,
            "blur_passes": 2
        },
        "animations": {
            "enabled": True,
            "preset": "Smooth"
        },
        "appearance": {
            "theme_name": "Catppuccin"
        }
    },
    "Laptop": {
        "description": "Power efficient: reduced blur passes, fast light animations, touchpad gestures",
        "windows": {
            "border_size": 2,
            "rounding": 6,
            "gaps_in": 4,
            "gaps_out": 8,
            "active_opacity": 1.0,
            "inactive_opacity": 0.95,
            "drop_shadow": False,
            "blur_enabled": False,
        },
        "animations": {
            "enabled": True,
            "preset": "Fast"
        },
        "input": {
            "touchpad_natural_scroll": True,
            "touchpad_tap_to_click": True,
            "touchpad_disable_while_typing": True
        },
        "appearance": {
            "theme_name": "Nord"
        }
    },
    "Minimal": {
        "description": "Clean and distraction-free: subtle borders, no shadows, fast responsive feel",
        "windows": {
            "border_size": 1,
            "rounding": 4,
            "gaps_in": 2,
            "gaps_out": 6,
            "active_opacity": 1.0,
            "inactive_opacity": 1.0,
            "drop_shadow": False,
            "blur_enabled": False
        },
        "animations": {
            "enabled": True,
            "preset": "Minimal"
        },
        "appearance": {
            "theme_name": "Dark"
        }
    },
    "Streaming": {
        "description": "Privacy & broadcast: full opacity on all windows, distinct active border glow",
        "windows": {
            "border_size": 3,
            "rounding": 8,
            "gaps_in": 8,
            "gaps_out": 16,
            "active_opacity": 1.0,
            "inactive_opacity": 1.0,
            "drop_shadow": True,
            "blur_enabled": True
        },
        "animations": {
            "enabled": True,
            "preset": "Smooth"
        },
        "appearance": {
            "theme_name": "Tokyo Night"
        }
    }
}


class ProfileManager:
    def __init__(self, profiles_dir: Optional[str] = None):
        if profiles_dir:
            self.profiles_dir = profiles_dir
        else:
            xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            self.profiles_dir = os.path.join(xdg_config, "hyprland-config-manager", "profiles")
        
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.state_file = os.path.join(self.profiles_dir, "current_profile.txt")
        self._initialize_defaults()

    def _initialize_defaults(self):
        for name, data in DEFAULT_PROFILES.items():
            path = self._get_profile_path(name)
            if not os.path.exists(path):
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass

    def _get_profile_path(self, name: str) -> str:
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        return os.path.join(self.profiles_dir, f"{safe_name}.json")

    def list_profiles(self) -> List[str]:
        profiles = []
        if os.path.exists(self.profiles_dir):
            for f in sorted(os.listdir(self.profiles_dir)):
                if f.endswith(".json") and not f.startswith("."):
                    profiles.append(f[:-5])
        return profiles

    def get_active_profile(self) -> str:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    curr = f.read().strip()
                    if curr in self.list_profiles():
                        return curr
            except Exception:
                pass
        return "Work" if "Work" in self.list_profiles() else (self.list_profiles()[0] if self.list_profiles() else "Default")

    def set_active_profile(self, name: str):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                f.write(name)
        except Exception:
            pass

    def load_profile(self, name: str) -> Optional[Dict[str, Any]]:
        path = self._get_profile_path(name)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save_profile(self, name: str, data: Dict[str, Any]) -> bool:
        path = self._get_profile_path(name)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        data = self.load_profile(source_name)
        if data is None:
            return False
        data["description"] = f"Copy of {source_name}"
        return self.save_profile(new_name, data)

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        old_path = self._get_profile_path(old_name)
        new_path = self._get_profile_path(new_name)
        if not os.path.exists(old_path) or os.path.exists(new_path):
            return False
        try:
            os.rename(old_path, new_path)
            if self.get_active_profile() == old_name:
                self.set_active_profile(new_name)
            return True
        except Exception:
            return False

    def delete_profile(self, name: str) -> bool:
        path = self._get_profile_path(name)
        if os.path.exists(path):
            try:
                os.remove(path)
                if self.get_active_profile() == name:
                    remaining = self.list_profiles()
                    self.set_active_profile(remaining[0] if remaining else "Default")
                return True
            except Exception:
                return False
        return False

    def export_profile(self, name: str, export_path: str) -> Tuple[bool, str]:
        src = self._get_profile_path(name)
        if not os.path.exists(src):
            return False, f"Profile '{name}' does not exist"
        try:
            shutil.copy2(src, export_path)
            return True, f"Profile exported to {export_path}"
        except Exception as e:
            return False, str(e)

    def import_profile(self, import_path: str) -> Tuple[bool, str]:
        if not os.path.exists(import_path):
            return False, f"File {import_path} does not exist"
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            base_name = os.path.splitext(os.path.basename(import_path))[0]
            # Avoid overwriting
            target_name = base_name
            counter = 1
            while target_name in self.list_profiles():
                target_name = f"{base_name}_{counter}"
                counter += 1
            self.save_profile(target_name, data)
            return True, target_name
        except Exception as e:
            return False, f"Invalid profile file: {str(e)}"
