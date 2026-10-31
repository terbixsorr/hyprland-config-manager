"""
Dashboard Page for Hyprland Config Manager.
Displays high-level compositor stats, active configuration status, and quick action buttons.
"""

from datetime import datetime
import os


class DashboardPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine
        self.hyprctl = main_window.hyprctl

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        page = Adw.PreferencesPage()
        page.set_title("Dashboard")
        page.set_icon_name("user-home-symbolic")

        # 1. System & Compositor Status Group
        status_grp = Adw.PreferencesGroup()
        status_grp.set_title("Compositor & Session Status")
        status_grp.set_description("Real-time telemetry and running environment")

        status = self.hyprctl.get_status()

        # Running Status Row
        row_status = Adw.ActionRow()
        row_status.set_title("Hyprland Status")
        if status.is_running:
            row_status.set_subtitle(f"Running • {status.version}")
            badge = Gtk.Label(label="ACTIVE")
            badge.add_css_class("status-dot-active")
        else:
            row_status.set_subtitle("Hyprland is not running (Offline / File Edit Mode)")
            badge = Gtk.Label(label="OFFLINE")
            badge.add_css_class("status-dot-inactive")
        row_status.add_suffix(badge)
        status_grp.add(row_status)

        # Monitors & Workspaces Row
        row_stats = Adw.ActionRow()
        row_stats.set_title("Display & Workspaces")
        mon_count = status.monitors_count if status.is_running else len(self.engine.monitors)
        ws_count = status.workspaces_count if status.is_running else len(self.engine.workspace_rules)
        row_stats.set_subtitle(f"{mon_count} Monitor(s) detected • {ws_count} Workspace(s) active")
        row_stats.set_icon_name("video-display-symbolic")
        status_grp.add(row_stats)

        # Active Window Row
        row_win = Adw.ActionRow()
        row_win.set_title("Focused Window")
        if status.active_window_class or status.active_window_title:
            row_win.set_subtitle(f"{status.active_window_class}: {status.active_window_title}")
        else:
            row_win.set_subtitle("None")
        row_win.set_icon_name("window-new-symbolic")
        status_grp.add(row_win)

        # Config File Info Row
        row_cfg = Adw.ActionRow()
        row_cfg.set_title("Configuration Target")
        mod_time = "Unknown"
        if os.path.exists(self.engine.config_path):
            mtime = os.path.getmtime(self.engine.config_path)
            mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        row_cfg.set_subtitle(f"{self.engine.config_path} (Last modified: {mod_time})")
        row_cfg.set_icon_name("text-x-generic-symbolic")
        status_grp.add(row_cfg)

        # Active Profile Row
        row_prof = Adw.ActionRow()
        row_prof.set_title("Active Profile")
        row_prof.set_subtitle(self.win.profile_mgr.get_active_profile())
        row_prof.set_icon_name("starred-symbolic")
        status_grp.add(row_prof)

        page.add(status_grp)

        # 2. Quick Actions Group
        action_grp = Adw.PreferencesGroup()
        action_grp.set_title("Quick Actions")
        action_grp.set_description("Apply changes, validate integrity, or perform manual snapshots")

        box_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_actions.set_margin_top(10)
        box_actions.set_margin_bottom(10)

        # [Apply Changes]
        btn_apply = Gtk.Button(label="Apply Changes")
        btn_apply.set_icon_name("emblem-ok-symbolic")
        btn_apply.add_css_class("btn-primary-apply")
        btn_apply.connect("clicked", lambda b: self.win.on_apply_clicked())
        box_actions.append(btn_apply)

        # [Reload Hyprland]
        btn_reload = Gtk.Button(label="Reload Hyprland")
        btn_reload.set_icon_name("view-refresh-symbolic")
        btn_reload.connect("clicked", lambda b: self.win.on_reload_clicked())
        box_actions.append(btn_reload)

        # [Validate Config]
        btn_validate = Gtk.Button(label="Validate Config")
        btn_validate.set_icon_name("dialog-information-symbolic")
        btn_validate.connect("clicked", lambda b: self.win.on_validate_clicked())
        box_actions.append(btn_validate)

        # [Backup Config]
        btn_backup = Gtk.Button(label="Backup Config")
        btn_backup.set_icon_name("document-save-symbolic")
        btn_backup.connect("clicked", lambda b: self.win.on_backup_clicked())
        box_actions.append(btn_backup)

        # [Restore Backup]
        btn_restore = Gtk.Button(label="Restore Backup")
        btn_restore.set_icon_name("edit-undo-symbolic")
        btn_restore.add_css_class("btn-rollback")
        btn_restore.connect("clicked", lambda b: self.win.on_restore_clicked())
        box_actions.append(btn_restore)

        action_grp.add(box_actions)
        page.add(action_grp)

        return page
