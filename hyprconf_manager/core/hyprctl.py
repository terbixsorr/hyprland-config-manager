"""
Hyprland Client & IPC integration.
Queries real Hyprland state via hyprctl and provides graceful offline fallback.
"""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class HyprlandStatus:
    is_running: bool = False
    version: str = "Unknown"
    commit: str = ""
    branch: str = ""
    monitors_count: int = 0
    workspaces_count: int = 0
    active_window_title: str = ""
    active_window_class: str = ""
    socket_path: str = ""
    instance_signature: str = ""


class HyprctlClient:
    def __init__(self):
        self.hyprctl_path = shutil.which("hyprctl")
        self.instance_signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")

    def is_available(self) -> bool:
        return self.hyprctl_path is not None

    def _run_cmd(self, args: List[str], timeout: float = 3.0) -> Tuple[int, str, str]:
        if not self.hyprctl_path:
            return 127, "", "hyprctl not found in PATH"
        try:
            cmd = [self.hyprctl_path] + args
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -2, "", str(e)

    def get_status(self) -> HyprlandStatus:
        status = HyprlandStatus()
        status.instance_signature = self.instance_signature

        if not self.is_available():
            status.is_running = False
            status.version = "hyprctl not installed"
            return status

        # Check version
        ret, stdout, stderr = self._run_cmd(["version"])
        if ret != 0 or "Hyprland" not in stdout:
            status.is_running = False
            status.version = "Hyprland is not running"
            return status

        status.is_running = True
        # Extract version tag: e.g. "Hyprland, built from branch main at commit ... (v0.41.2)"
        for line in stdout.splitlines():
            line_str = line.strip()
            if "Hyprland, built from" in line_str or "version" in line_str.lower():
                status.version = line_str
                break
        if status.version == "Unknown" and stdout:
            status.version = stdout.splitlines()[0]

        # Get monitors count
        monitors = self.get_monitors()
        status.monitors_count = len(monitors)

        # Get workspaces count
        workspaces = self.get_workspaces()
        status.workspaces_count = len(workspaces)

        # Get active window
        active_win = self.get_active_window()
        if active_win:
            status.active_window_title = active_win.get("title", "")
            status.active_window_class = active_win.get("class", "")

        return status

    def get_monitors(self) -> List[Dict[str, Any]]:
        """Returns JSON output from `hyprctl -j monitors`"""
        ret, stdout, _ = self._run_cmd(["-j", "monitors"])
        if ret == 0 and stdout:
            try:
                data = json.loads(stdout)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
        return []

    def get_workspaces(self) -> List[Dict[str, Any]]:
        """Returns JSON output from `hyprctl -j workspaces`"""
        ret, stdout, _ = self._run_cmd(["-j", "workspaces"])
        if ret == 0 and stdout:
            try:
                data = json.loads(stdout)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
        return []

    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Returns JSON output from `hyprctl -j activewindow`"""
        ret, stdout, _ = self._run_cmd(["-j", "activewindow"])
        if ret == 0 and stdout:
            try:
                data = json.loads(stdout)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
        return None

    def reload(self) -> Tuple[bool, str]:
        """Runs `hyprctl reload`"""
        ret, stdout, stderr = self._run_cmd(["reload"])
        if ret == 0:
            return True, stdout.strip() or "Hyprland reloaded successfully."
        return False, stderr.strip() or stdout.strip() or f"Reload failed with exit code {ret}"

    def set_keyword(self, key: str, value: str) -> Tuple[bool, str]:
        """Runs `hyprctl keyword <key> <value>` to preview settings in real time"""
        ret, stdout, stderr = self._run_cmd(["keyword", key, value])
        if ret == 0:
            return True, stdout.strip()
        return False, stderr.strip() or stdout.strip()
