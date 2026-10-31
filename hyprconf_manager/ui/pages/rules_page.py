"""
Window Rules Page for Hyprland Config Manager.
Provides an intuitive GUI builder for windowrulev2 without requiring raw regex syntax.
"""

from typing import Optional
from ...core.models import WindowRuleItem


class RulesPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        page = Adw.PreferencesPage()
        page.set_title("Rules")
        page.set_icon_name("preferences-desktop-display-symbolic")

        grp_top = Adw.PreferencesGroup()
        grp_top.set_title("Window Rules (windowrulev2)")
        grp_top.set_description("Auto-float, resize, position, set opacity, or assign windows to workspaces by class and title")

        btn_add = Gtk.Button(label="Create Window Rule")
        btn_add.set_icon_name("list-add-symbolic")
        btn_add.add_css_class("suggested-action")
        btn_add.connect("clicked", lambda b: self._show_rule_dialog())
        grp_top.add(btn_add)
        page.add(grp_top)

        grp_list = Adw.PreferencesGroup()
        grp_list.set_title("Configured Rules")

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")

        self._populate_list()
        grp_list.add(self.list_box)
        page.add(grp_list)

        return page

    def _populate_list(self):
        try:
            from gi.repository import Gtk, Adw
        except ImportError:
            return

        while True:
            child = self.list_box.get_first_child()
            if not child:
                break
            self.list_box.remove(child)

        if not self.engine.window_rules:
            empty_row = Adw.ActionRow()
            empty_row.set_title("No custom window rules defined")
            empty_row.set_subtitle("Click 'Create Window Rule' above to add automatic window behaviors")
            self.list_box.append(empty_row)
            return

        for rule in self.engine.window_rules:
            row = Adw.ActionRow()
            title = f"Class: {rule.app_class}" if rule.app_class else (f"Title: {rule.app_title}" if rule.app_title else "Window Rule")
            row.set_title(title)
            row.set_subtitle(rule.to_directive())

            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            btn_edit = Gtk.Button()
            btn_edit.set_icon_name("document-edit-symbolic")
            btn_edit.set_tooltip_text("Edit this rule")
            btn_edit.connect("clicked", self._make_edit_handler(rule))
            btn_box.append(btn_edit)

            btn_del = Gtk.Button()
            btn_del.set_icon_name("user-trash-symbolic")
            btn_del.set_tooltip_text("Delete this rule")
            btn_del.connect("clicked", self._make_delete_handler(rule))
            btn_box.append(btn_del)

            row.add_suffix(btn_box)
            self.list_box.append(row)

    def _make_edit_handler(self, rule: WindowRuleItem):
        def handler(button):
            self._show_rule_dialog(existing_rule=rule)
        return handler

    def _make_delete_handler(self, rule: WindowRuleItem):
        def handler(button):
            if rule in self.engine.window_rules:
                self.engine.window_rules.remove(rule)
                self.win.mark_modified()
                self._populate_list()
        return handler

    def _show_rule_dialog(self, existing_rule: Optional[WindowRuleItem] = None):
        try:
            from gi.repository import Gtk, Adw
        except ImportError:
            return

        is_edit = existing_rule is not None
        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Edit Window Rule" if is_edit else "Create Window Rule"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save Changes" if is_edit else "Create Rule")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        entry_class = Adw.EntryRow()
        entry_class.set_title("Window Class (e.g. kitty, firefox, pavucontrol)")
        if is_edit and existing_rule.app_class:
            entry_class.set_text(existing_rule.app_class)
        box.append(entry_class)

        entry_title = Adw.EntryRow()
        entry_title.set_title("Window Title (optional substring/regex)")
        if is_edit and existing_rule.app_title:
            entry_title.set_text(existing_rule.app_title)
        box.append(entry_title)

        sw_float = Adw.SwitchRow()
        sw_float.set_title("Float Window")
        if is_edit and existing_rule.floating:
            sw_float.set_active(True)
        box.append(sw_float)

        sw_full = Adw.SwitchRow()
        sw_full.set_title("Fullscreen on Open")
        if is_edit and existing_rule.fullscreen:
            sw_full.set_active(True)
        box.append(sw_full)

        entry_ws = Adw.EntryRow()
        entry_ws.set_title("Assign to Workspace (e.g. 2, special:scratch)")
        if is_edit and existing_rule.workspace:
            entry_ws.set_text(existing_rule.workspace)
        box.append(entry_ws)

        entry_opacity = Adw.EntryRow()
        entry_opacity.set_title("Opacity (e.g. 0.85, 0.95)")
        if is_edit and existing_rule.opacity is not None:
            entry_opacity.set_text(str(existing_rule.opacity))
        box.append(entry_opacity)

        entry_size = Adw.EntryRow()
        entry_size.set_title("Size (e.g. 800 600)")
        if is_edit and existing_rule.size:
            entry_size.set_text(existing_rule.size)
        box.append(entry_size)

        entry_pos = Adw.EntryRow()
        entry_pos.set_title("Position (e.g. center, 100 100)")
        if is_edit and existing_rule.position:
            entry_pos.set_text(existing_rule.position)
        box.append(entry_pos)

        dialog.set_extra_child(box)

        def on_response(dlg, response_id):
            if response_id == "save":
                cls_name = entry_class.get_text().strip()
                title_name = entry_title.get_text().strip()
                if not cls_name and not title_name:
                    return

                opacity_val = None
                raw_op = entry_opacity.get_text().strip()
                if raw_op:
                    try:
                        opacity_val = float(raw_op)
                    except ValueError:
                        opacity_val = None

                target_rule = existing_rule if is_edit else WindowRuleItem()
                target_rule.app_class = cls_name
                target_rule.app_title = title_name
                target_rule.floating = sw_float.get_active() or None
                target_rule.fullscreen = sw_full.get_active() or None
                target_rule.workspace = entry_ws.get_text().strip() or None
                target_rule.opacity = opacity_val
                target_rule.size = entry_size.get_text().strip() or None
                target_rule.position = entry_pos.get_text().strip() or None
                target_rule.raw_rule = ""  # Trigger clean regeneration

                if not is_edit:
                    self.engine.window_rules.append(target_rule)

                self.win.mark_modified()
                self._populate_list()

        dialog.connect("response", on_response)
        dialog.present()
