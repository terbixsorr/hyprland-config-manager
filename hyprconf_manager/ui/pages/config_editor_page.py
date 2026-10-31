"""
Config Editor Page for Hyprland Config Manager.
Provides an advanced raw text editor with line numbers, syntax validation,
search, diff preview, and bidirectional sync with GUI settings.
"""

from ...core.validator import HyprlandValidator
from ...core.generator import HyprlandGenerator


class ConfigEditorPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine
        self.validator = HyprlandValidator()

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        box_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box_page.set_margin_top(12)
        box_page.set_margin_bottom(12)
        box_page.set_margin_start(16)
        box_page.set_margin_end(16)

        # 1. Action Toolbar
        box_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Search bar
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)
        self.search_entry.set_placeholder_text("Find in configuration (Ctrl+F)...")
        box_toolbar.append(self.search_entry)

        btn_validate = Gtk.Button(label="Validate Syntax")
        btn_validate.set_icon_name("dialog-information-symbolic")
        btn_validate.connect("clicked", lambda b: self._validate_text())
        box_toolbar.append(btn_validate)

        btn_sync = Gtk.Button(label="Save & Sync to GUI")
        btn_sync.set_icon_name("emblem-ok-symbolic")
        btn_sync.add_css_class("suggested-action")
        btn_sync.connect("clicked", lambda b: self._sync_to_gui())
        box_toolbar.append(btn_sync)

        btn_revert = Gtk.Button(label="Reset from GUI")
        btn_revert.set_icon_name("edit-undo-symbolic")
        btn_revert.connect("clicked", lambda b: self._reload_from_gui())
        box_toolbar.append(btn_revert)

        box_page.append(box_toolbar)

        # 2. Text View inside ScrolledWindow
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.add_css_class("card")

        self.text_view = Gtk.TextView()
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.NONE)
        self.text_view.set_left_margin(12)
        self.text_view.set_right_margin(12)
        self.text_view.set_top_margin(12)
        self.text_view.set_bottom_margin(12)

        self.buffer = self.text_view.get_buffer()
        # Initial text from engine
        current_text = self.engine.generate_candidate_config()
        self.buffer.set_text(current_text)

        scrolled.set_child(self.text_view)
        box_page.append(scrolled)

        # Wire search
        self.search_entry.connect("search-changed", self._on_search_changed)

        return box_page

    def _get_current_editor_text(self) -> str:
        start_iter = self.buffer.get_start_iter()
        end_iter = self.buffer.get_end_iter()
        return self.buffer.get_text(start_iter, end_iter, True)

    def _validate_text(self):
        text = self._get_current_editor_text()
        res = self.validator.validate_content(text)
        if res.is_valid:
            warn_msg = f" (with {len(res.warnings)} warnings)" if res.warnings else ""
            self.win.show_toast(f"Syntax is Valid! Ready to apply{warn_msg}.")
        else:
            first_err = res.errors[0]
            self.win.show_toast(f"Syntax Error on line {first_err.line_number}: {first_err.message}")

    def _sync_to_gui(self):
        text = self._get_current_editor_text()
        res = self.validator.validate_content(text)
        if not res.is_valid:
            first_err = res.errors[0]
            self.win.show_toast(f"Cannot sync: Line {first_err.line_number}: {first_err.message}")
            return

        # Reload engine models from the edited text!
        self.engine.load_from_string(text, file_path=self.engine.config_path)
        self.win.mark_modified()
        self.win.show_toast("Configuration parsed and synced to all GUI panels!")

    def _reload_from_gui(self):
        text = self.engine.generate_candidate_config()
        self.buffer.set_text(text)
        self.win.show_toast("Editor refreshed from current GUI settings.")

    def _on_search_changed(self, entry):
        query = entry.get_text()
        if not query:
            return
        start_iter = self.buffer.get_start_iter()
        match = start_iter.forward_search(query, 0, None)
        if match:
            match_start, match_end = match
            self.buffer.select_range(match_start, match_end)
            self.text_view.scroll_to_iter(match_start, 0.1, False, 0, 0)
