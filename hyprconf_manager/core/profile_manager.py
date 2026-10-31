"""
Profile Manager for Hyprland Config Manager.
Allows saving, switching, exporting, importing, and activating named profiles
such as Gaming, Work, Laptop, Minimal, and Streaming with strict JSON validation.
"""

import json
import os
import shutil
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple


def validate_profile_dict(data: Any) -> Tuple[bool, str]:
    """
    Validates structure, keys, and types of a profile dictionary.
    Returns (True, "") if valid, or (False, "Reason...") if invalid.
    """
    if not isinstance(data, dict):
        return False, "Profile root must be a JSON object (dictionary)."

    allowed_top_keys = {"name", "description", "windows", "animations", "appearance", "input", "env"}
    unknown_keys = set(data.keys()) - allowed_top_keys
    if unknown_keys:
        return False, f"Profile contains unknown top-level section(s): {', '.join(unknown_keys)}"

    # Validate name and description
    if "name" in data and not isinstance(data["name"], str):
        return False, "Property 'name' must be a string."
    if "description" in data and not isinstance(data["description"], str):
        return False, "Property 'description' must be a string."

    # Validate windows section
    if "windows" in data:
        w = data["windows"]
        if not isinstance(w, dict):
            return False, "Section 'windows' must be a JSON object."
        int_non_neg_fields = [
            "border_size", "rounding", "gaps_in", "gaps_out", "shadow_range",
            "shadow_render_power", "blur_size", "blur_passes"
        ]
        for field in int_non_neg_fields:
            if field in w:
                val = w[field]
                if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                    return False, f"'windows.{field}' must be a non-negative integer."

        for op_field in ("active_opacity", "inactive_opacity", "fullscreen_opacity"):
            if op_field in w:
                val = w[op_field]
                if not isinstance(val, (int, float)) or isinstance(val, bool) or not (0.0 <= val <= 1.0):
                    return False, f"'windows.{op_field}' must be a float between 0.0 and 1.0."

        for b_field in ("drop_shadow", "blur_enabled", "blur_new_optimizations"):
            if b_field in w and not isinstance(w[b_field], bool):
                return False, f"'windows.{b_field}' must be a boolean (true/false)."

        if "layout" in w and w["layout"] not in ("dwindle", "master"):
            return False, "'windows.layout' must be either 'dwindle' or 'master'."

    # Validate animations section
    if "animations" in data:
        a = data["animations"]
        if not isinstance(a, dict):
            return False, "Section 'animations' must be a JSON object."
        if "enabled" in a and not isinstance(a["enabled"], bool):
            return False, "'animations.enabled' must be a boolean."
        if "preset" in a and not isinstance(a["preset"], str):
            return False, "'animations.preset' must be a string."
        if "bezier_curves" in a:
            if not isinstance(a["bezier_curves"], dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in a["bezier_curves"].items()):
                return False, "'animations.bezier_curves' must be an object of curve names and coordinate strings."

    # Validate appearance section
    if "appearance" in data:
        app = data["appearance"]
        if not isinstance(app, dict):
            return False, "Section 'appearance' must be a JSON object."
        for str_field in ("theme_name", "col_active_border", "col_inactive_border"):
            if str_field in app and not isinstance(app[str_field], str):
                return False, f"'appearance.{str_field}' must be a string."
        if "rounding" in app:
            val = app["rounding"]
            if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                return False, "'appearance.rounding' must be a non-negative integer."

    # Validate input section
    if "input" in data:
        inp = data["input"]
        if not isinstance(inp, dict):
            return False, "Section 'input' must be a JSON object."
        for sens_field in ("sensitivity", "mouse_sensitivity"):
            if sens_field in inp:
                val = inp[sens_field]
                if not isinstance(val, (int, float)) or isinstance(val, bool) or not (-1.0 <= val <= 1.0):
                    return False, f"'input.{sens_field}' must be a number between -1.0 and 1.0."
        if "accel_profile" in inp and inp["accel_profile"] not in ("adaptive", "flat", "custom"):
            return False, "'input.accel_profile' must be one of: adaptive, flat, custom."
        for bool_field in (
            "natural_scroll", "touchpad_natural_scroll", "touchpad_tap_to_click",
            "touchpad_drag_lock", "touchpad_disable_while_typing", "numlock_by_default"
        ):
            if bool_field in inp and not isinstance(inp[bool_field], bool):
                return False, f"'input.{bool_field}' must be a boolean."
        for int_pos_field in ("repeat_rate", "repeat_delay"):
            if int_pos_field in inp:
                val = inp[int_pos_field]
                if not isinstance(val, int) or isinstance(val, bool) or val <= 0:
                    return False, f"'input.{int_pos_field}' must be a positive integer."

    # Validate env section
    if "env" in data:
        e = data["env"]
        if not isinstance(e, dict) or not all(isinstance(k, str) and isinstance(v, (str, int, float)) for k, v in e.items()):
            return False, "Section 'env' must be an object mapping variable names to string values."

    return True, ""


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
                data = json.load(f)
                valid, _ = validate_profile_dict(data)
                return data if valid else None
        except Exception:
            return None

    def save_profile(self, name: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        valid, msg = validate_profile_dict(data)
        if not valid:
            return False, f"Validation error: {msg}"

        path = self._get_profile_path(name)
        tmp_path = f"{path}.tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
            return True, ""
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return False, f"Failed to save profile: {e}"

    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        data = self.load_profile(source_name)
        if data is None:
            return False
        data["description"] = f"Copy of {source_name}"
        ok, _ = self.save_profile(new_name, data)
        return ok

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
        except json.JSONDecodeError as jde:
            return False, f"Malformed JSON syntax: {jde}"
        except Exception as e:
            return False, f"Error reading file: {e}"

        valid, err_msg = validate_profile_dict(data)
        if not valid:
            return False, f"Invalid profile format: {err_msg}"

        base_name = os.path.splitext(os.path.basename(import_path))[0]
        # Sanitize name
        clean_name = "".join(c for c in base_name if c.isalnum() or c in ("-", "_")).strip() or "ImportedProfile"
        target_name = clean_name
        counter = 1
        while target_name in self.list_profiles():
            target_name = f"{clean_name}_{counter}"
            counter += 1

        ok, save_err = self.save_profile(target_name, data)
        if not ok:
            return False, save_err
        return True, target_name
