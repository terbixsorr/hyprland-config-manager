"""
Window Rules Page for Hyprland Config Manager.
Provides an intuitive GUI builder for windowrulev2 without requiring raw regex syntax.
"""

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
        grp_top.set_description("Auto-float, resize, position, or assign windows to workspaces by class and title")

        btn_add = Gtk.Button(label="Create Window Rule")
        btn_add.set_icon_name("list-add-symbolic")
        btn_add.add_css_class("suggested-action")
        btn_add.connect("clicked", lambda b: self._show_add_dialog())
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

        for rule in self.engine.window_rules:
            row = Adw.ActionRow()
            title = f"Class: {rule.app_class}" if rule.app_class else (rule.app_title or "Rule")
            row.set_title(title)
            row.set_subtitle(rule.to_directive())

            btn_del = Gtk.Button()
            btn_del.set_icon_name("user-trash-symbolic")
            btn_del.connect("clicked", self._make_delete_handler(rule))
            row.add_suffix(btn_del)

            self.list_box.append(row)

    def _make_delete_handler(self, rule: WindowRuleItem):
        def handler(button):
            if rule in self.engine.window_rules:
                self.engine.window_rules.remove(rule)
                self.win.mark_modified()
                self._populate_list()
        return handler

    def _show_add_dialog(self):
        try:
            from gi.repository import Gtk, Adw
        except ImportError:
            return

        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Create Window Rule"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save Rule")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        entry_class = Adw.EntryRow()
        entry_class.set_title("Window Class (e.g. kitty, firefox, pavucontrol)")
        box.append(entry_class)

        entry_title = Adw.EntryRow()
        entry_title.set_title("Window Title (optional substring/regex)")
        box.append(entry_title)

        sw_float = Adw.SwitchRow()
        sw_float.set_title("Float Window")
        box.append(sw_float)

        sw_full = Adw.SwitchRow()
        sw_full.set_title("Fullscreen on Open")
        box.append(sw_full)

        entry_ws = Adw.EntryRow()
        entry_ws.set_title("Assign to Workspace (e.g. 2, special:scratch)")
        box.append(entry_ws)

        entry_size = Adw.EntryRow()
        entry_size.set_title("Size (e.g. 800 600)")
        box.append(entry_size)

        entry_pos = Adw.EntryRow()
        entry_pos.set_title("Position (e.g. center, 100 100)")
        box.append(entry_pos)

        dialog.set_extra_child(box)

        def on_response(dlg, response_id):
            if response_id == "save":
                cls_name = entry_class.get_text().strip()
                if cls_name or entry_title.get_text().strip():
                    new_rule = WindowRuleItem(
                        app_class=cls_name,
                        app_title=entry_title.get_text().strip(),
                        floating=sw_float.get_active() or None,
                        fullscreen=sw_full.get_active() or None,
                        workspace=entry_ws.get_text().strip() or None,
                        size=entry_size.get_text().strip() or None,
                        position=entry_pos.get_text().strip() or None
                    )
                    self.engine.window_rules.append(new_rule)
                    self.win.mark_modified()
                    self._populate_list()

        dialog.connect("response", on_response)
        dialog.present()
