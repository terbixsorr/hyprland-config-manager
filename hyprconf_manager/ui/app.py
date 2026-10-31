"""
Main GTK4 + Libadwaita Application Window for Hyprland Config Manager.
Provides modern Linux desktop settings UI, sidebar navigation, bottom status bar,
diff inspection dialog, toast notifications, and safe apply transactions.
"""

import os
from typing import Optional

from ..core.config_engine import HyprlandConfigEngine
from ..core.backup_manager import BackupManager
from ..core.validator import HyprlandValidator
from ..core.hyprctl import HyprctlClient
from ..core.profile_manager import ProfileManager
from ..core.safe_apply import SafeApplyPipeline
from .style import apply_custom_css
from .pages import (
    DashboardPageBuilder,
    MonitorsPageBuilder,
    WindowsPageBuilder,
    AppearancePageBuilder,
    AnimationsPageBuilder,
    InputPageBuilder,
    KeybindsPageBuilder,
    StartupPageBuilder,
    WorkspacesPageBuilder,
    RulesPageBuilder,
    WallpapersPageBuilder,
    EnvironmentPageBuilder,
    AdvancedPageBuilder,
    ProfilesPageBuilder,
    ConfigEditorPageBuilder,
    BackupsPageBuilder,
)


class MainWindow:
    """
    Controller & wrapper for the Adw.ApplicationWindow.
    """
    def __init__(self, app, config_path: Optional[str] = None):
        self.app = app
        self.engine = HyprlandConfigEngine(config_path=config_path)
        self.backup_mgr = BackupManager()
        self.validator = HyprlandValidator()
        self.hyprctl = HyprctlClient()
        self.profile_mgr = ProfileManager()
        self.safe_apply = SafeApplyPipeline(self.backup_mgr, self.validator, self.hyprctl)

        self.is_modified = False
        self.window = None
        self.toast_overlay = None
        self.stack = None
        self.status_label = None
        self.version_label = None
        self.status_dot = None

        # Load initial config
        self.engine.load_file()

        # Build GUI
        self._build_ui()

    def _build_ui(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return

        self.window = Adw.ApplicationWindow(application=self.app)
        self.window.set_title("Hyprland Config Manager")
        self.window.set_default_size(1120, 780)
        self.window.add_css_class("hypr-window")

        # Main vertical box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header bar
        header = Adw.HeaderBar()
        header.set_show_title(True)

        btn_apply_top = Gtk.Button(label="Apply")
        btn_apply_top.set_icon_name("emblem-ok-symbolic")
        btn_apply_top.add_css_class("btn-primary-apply")
        btn_apply_top.connect("clicked", lambda b: self.on_apply_clicked())
        header.pack_end(btn_apply_top)

        btn_reload_top = Gtk.Button()
        btn_reload_top.set_icon_name("view-refresh-symbolic")
        btn_reload_top.set_tooltip_text("Reload Hyprland Compositor")
        btn_reload_top.connect("clicked", lambda b: self.on_reload_clicked())
        header.pack_end(btn_reload_top)

        main_box.append(header)

        # Toast overlay
        self.toast_overlay = Adw.ToastOverlay()
        main_box.append(self.toast_overlay)

        # Navigation Split View (Sidebar + Content View)
        split_view = Adw.NavigationSplitView()
        split_view.set_vexpand(True)
        split_view.set_hexpand(True)
        split_view.set_min_sidebar_width(220)
        split_view.set_max_sidebar_width(280)

        # Stack & Sidebar
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)

        sidebar = Gtk.StackSidebar()
        sidebar.set_stack(self.stack)
        sidebar.add_css_class("hypr-sidebar")

        # Pages Definition
        pages_def = [
            ("dashboard", "Dashboard", DashboardPageBuilder(self).build),
            ("monitors", "Monitors", MonitorsPageBuilder(self).build),
            ("windows", "Windows", WindowsPageBuilder(self).build),
            ("appearance", "Appearance", AppearancePageBuilder(self).build),
            ("animations", "Animations", AnimationsPageBuilder(self).build),
            ("input", "Input", InputPageBuilder(self).build),
            ("keybinds", "Keybinds", KeybindsPageBuilder(self).build),
            ("startup", "Startup", StartupPageBuilder(self).build),
            ("workspaces", "Workspaces", WorkspacesPageBuilder(self).build),
            ("rules", "Window Rules", RulesPageBuilder(self).build),
            ("wallpapers", "Wallpapers", WallpapersPageBuilder(self).build),
            ("environment", "Environment", EnvironmentPageBuilder(self).build),
            ("advanced", "Advanced", AdvancedPageBuilder(self).build),
            ("profiles", "Profiles", ProfilesPageBuilder(self).build),
            ("editor", "Config Editor", ConfigEditorPageBuilder(self).build),
            ("backups", "Backups", BackupsPageBuilder(self).build),
        ]

        for p_id, p_title, p_builder in pages_def:
            child_widget = p_builder()
            if child_widget:
                self.stack.add_titled(child_widget, p_id, p_title)

        # Wrap sidebar and stack in NavigationPages
        nav_sidebar = Adw.NavigationPage.new(sidebar, "Settings")
        nav_content = Adw.NavigationPage.new(self.stack, "Detail")

        split_view.set_sidebar(nav_sidebar)
        split_view.set_content(nav_content)

        # Wrap in vertical layout with bottom bar
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_box.append(split_view)

        # Bottom Bar
        bottom_bar = self._build_bottom_bar()
        content_box.append(bottom_bar)

        self.toast_overlay.set_child(content_box)
        self.window.set_content(main_box)

    def _build_bottom_bar(self):
        try:
            from gi.repository import Gtk
        except ImportError:
            return None

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bar.set_margin_start(16)
        bar.set_margin_end(16)
        bar.set_margin_top(8)
        bar.set_margin_bottom(8)
        bar.add_css_class("card")

        # Left status indicators
        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        left_box.set_hexpand(True)

        self.status_dot = Gtk.Label(label="●")
        self.status_label = Gtk.Label()
        self.version_label = Gtk.Label()

        status = self.hyprctl.get_status()
        if status.is_running:
            self.status_dot.add_css_class("status-dot-active")
            self.status_label.set_text("Hyprland Active")
            self.version_label.set_text(f"• {status.version}")
        else:
            self.status_dot.add_css_class("status-dot-inactive")
            self.status_label.set_text("Hyprland Offline (File Edit Mode)")
            self.version_label.set_text("")

        self.status_label.set_margin_start(4)
        left_box.append(self.status_dot)
        left_box.append(self.status_label)
        left_box.append(self.version_label)
        bar.append(left_box)

        # Right quick buttons
        right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Rollback button
        btn_rollback = Gtk.Button(label="Rollback")
        btn_rollback.set_icon_name("edit-undo-symbolic")
        btn_rollback.add_css_class("btn-rollback")
        btn_rollback.connect("clicked", lambda b: self.on_rollback_clicked())
        right_box.append(btn_rollback)

        # Reload button
        btn_reload = Gtk.Button(label="Reload")
        btn_reload.set_icon_name("view-refresh-symbolic")
        btn_reload.connect("clicked", lambda b: self.on_reload_clicked())
        right_box.append(btn_reload)

        # Apply button
        btn_apply = Gtk.Button(label="Apply Changes")
        btn_apply.set_icon_name("emblem-ok-symbolic")
        btn_apply.add_css_class("btn-primary-apply")
        btn_apply.connect("clicked", lambda b: self.on_apply_clicked())
        right_box.append(btn_apply)

        bar.append(right_box)
        return bar

    def show(self):
        if self.window:
            self.window.present()

    def show_toast(self, message: str, timeout: int = 3):
        try:
            from gi.repository import Adw
            if self.toast_overlay:
                toast = Adw.Toast.new(message)
                toast.set_timeout(timeout)
                self.toast_overlay.add_toast(toast)
        except Exception:
            pass

    def mark_modified(self):
        self.is_modified = True
        if self.status_label:
            prefix = "● [Modified] "
            curr = self.status_label.get_text()
            if not curr.startswith("● [Modified]"):
                self.status_label.set_text(f"{prefix}{curr}")

    def on_apply_clicked(self):
        result = self.safe_apply.apply(self.engine)
        if result.success:
            self.is_modified = False
            self.show_toast(result.message)
            # Update status
            status = self.hyprctl.get_status()
            if status.is_running:
                self.status_label.set_text("Hyprland Active (Synced)")
            else:
                self.status_label.set_text("Config Saved (Offline)")
        else:
            self.show_error_dialog("Failed to Apply Configuration", result.message, result.details)

    def on_reload_clicked(self):
        ok, msg = self.hyprctl.reload()
        if ok:
            self.show_toast("Hyprland reloaded successfully!")
        else:
            self.show_toast(f"Reload failed: {msg}")

    def on_rollback_clicked(self):
        ok, msg = self.safe_apply.rollback(self.engine)
        if ok:
            self.is_modified = False
            self.show_toast("Rollback executed! Configuration restored.")
            self.refresh_all_pages()
        else:
            self.show_toast(f"Rollback failed: {msg}")

    def on_validate_clicked(self):
        candidate = self.engine.generate_candidate_config()
        res = self.validator.validate_content(candidate)
        if res.is_valid:
            warn_txt = f"\n\nWarnings:\n" + "\n".join([f"• Line {w.line_number}: {w.message}" for w in res.warnings]) if res.warnings else ""
            self.show_info_dialog("Configuration Valid", f"No errors found. Configuration is safe to apply.{warn_txt}")
        else:
            err_txt = "\n".join([f"• Line {e.line_number}: {e.message}\n  Explanation: {e.explanation}" for e in res.errors])
            self.show_error_dialog("Validation Failed", "Errors found in candidate configuration:", err_txt)

    def on_backup_clicked(self):
        curr = self.engine.generate_candidate_config()
        entry = self.backup_mgr.create_backup(curr, reason="Manual user backup from Dashboard")
        self.show_toast(f"Backup created: {entry.timestamp}")

    def on_restore_clicked(self):
        latest = self.backup_mgr.get_latest_backup()
        if not latest:
            self.show_toast("No backups available.")
            return
        self.on_rollback_clicked()

    def activate_profile(self, name: str):
        data = self.profile_mgr.load_profile(name)
        if not data:
            self.show_toast(f"Profile {name} not found.")
            return

        # Auto backup current before profile switch
        self.backup_mgr.create_backup(self.engine.generate_candidate_config(), reason=f"Auto backup before activating profile '{name}'")

        # Apply profile data to models
        if "windows" in data:
            w_data = data["windows"]
            for k, v in w_data.items():
                if hasattr(self.engine.windows, k):
                    setattr(self.engine.windows, k, v)

        if "animations" in data:
            a_data = data["animations"]
            if "enabled" in a_data:
                self.engine.animations.enabled = a_data["enabled"]
            if "preset" in a_data:
                self.engine.animations.preset = a_data["preset"]

        if "appearance" in data:
            app_data = data["appearance"]
            if "theme_name" in app_data:
                self.engine.appearance.theme_name = app_data["theme_name"]

        self.profile_mgr.set_active_profile(name)
        self.mark_modified()
        self.show_toast(f"Profile '{name}' activated! Click [Apply] to write to compositor.")
        self.refresh_all_pages()

    def refresh_all_pages(self):
        # Refresh current page view by switching stack
        cur = self.stack.get_visible_child_name() if self.stack else None
        if cur:
            self.stack.set_visible_child_name(cur)

    def refresh_current_page(self):
        self.refresh_all_pages()

    def show_diff_dialog(self, diff_text: str):
        try:
            from gi.repository import Gtk, Adw
            dialog = Adw.MessageDialog(transient_for=self.window, heading="Configuration Diff")
            dialog.add_response("close", "Close")

            scrolled = Gtk.ScrolledWindow()
            scrolled.set_min_content_width(650)
            scrolled.set_min_content_height(400)

            tv = Gtk.TextView()
            tv.set_monospace(True)
            tv.set_editable(False)
            tv.get_buffer().set_text(diff_text)
            scrolled.set_child(tv)

            dialog.set_extra_child(scrolled)
            dialog.present()
        except Exception:
            pass

    def show_error_dialog(self, heading: str, body: str, details: str = ""):
        try:
            from gi.repository import Gtk, Adw
            dialog = Adw.MessageDialog(transient_for=self.window, heading=heading, body=body)
            dialog.add_response("close", "Close")
            dialog.add_response("rollback", "Rollback to Backup")
            dialog.add_response("editor", "Open Config Editor")
            dialog.set_response_appearance("rollback", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_response_appearance("editor", Adw.ResponseAppearance.SUGGESTED)

            if details:
                scrolled = Gtk.ScrolledWindow()
                scrolled.set_min_content_width(500)
                scrolled.set_min_content_height(180)
                tv = Gtk.TextView()
                tv.set_monospace(True)
                tv.set_editable(False)
                tv.get_buffer().set_text(details)
                scrolled.set_child(tv)
                dialog.set_extra_child(scrolled)

            def on_response(dlg, response_id):
                if response_id == "rollback":
                    self.on_rollback_clicked()
                elif response_id == "editor":
                    if self.stack:
                        self.stack.set_visible_child_name("editor")

            dialog.connect("response", on_response)
            dialog.present()
        except Exception:
            pass

    def show_info_dialog(self, heading: str, body: str):
        try:
            from gi.repository import Adw
            dialog = Adw.MessageDialog(transient_for=self.window, heading=heading, body=body)
            dialog.add_response("ok", "OK")
            dialog.present()
        except Exception:
            pass


class HyprlandConfigApp:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.adw_app = None
        self.main_window = None

    def run(self, argv: list = None) -> int:
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Adw, Gio
        except (ImportError, ValueError) as e:
            print(f"[Hyprland Config Manager] GTK4 / Libadwaita unavailable: {e}")
            print("Note: To run the GUI, install 'gtk4', 'libadwaita', and 'python-gobject' on Arch Linux.")
            return 1

        self.adw_app = Adw.Application(
            application_id="io.github.hyprconf_manager",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )

        def on_activate(app):
            apply_custom_css()
            self.main_window = MainWindow(app, config_path=self.config_path)
            self.main_window.show()

        self.adw_app.connect("activate", on_activate)
        return self.adw_app.run(argv or [])
