"""
Environment Variables Page for Hyprland Config Manager.
Allows managing runtime environment variables (env = KEY,VALUE).
"""


class EnvironmentPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine
        self.cfg = main_window.engine.env_cfg

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        page = Adw.PreferencesPage()
        page.set_title("Environment")
        page.set_icon_name("system-software-install-symbolic")

        grp_top = Adw.PreferencesGroup()
        grp_top.set_title("Environment Variables (env = KEY,VALUE)")
        grp_top.set_description("Wayland platform hints, cursor sizes, and toolkit integrations")

        btn_add = Gtk.Button(label="Add Environment Variable")
        btn_add.set_icon_name("list-add-symbolic")
        btn_add.add_css_class("suggested-action")
        btn_add.connect("clicked", lambda b: self._show_add_dialog())
        grp_top.add(btn_add)
        page.add(grp_top)

        grp_list = Adw.PreferencesGroup()
        grp_list.set_title("Active Variables")

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

        for key, val in self.cfg.vars.items():
            row = Adw.ActionRow()
            row.set_title(key)
            row.set_subtitle(val)

            btn_del = Gtk.Button()
            btn_del.set_icon_name("user-trash-symbolic")
            btn_del.connect("clicked", self._make_delete_handler(key))
            row.add_suffix(btn_del)

            self.list_box.append(row)

    def _make_delete_handler(self, key: str):
        def handler(button):
            if key in self.cfg.vars:
                del self.cfg.vars[key]
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
            heading="Add Environment Variable"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        entry_key = Adw.EntryRow()
        entry_key.set_title("Variable Name (e.g. XCURSOR_SIZE, QT_QPA_PLATFORM)")
        box.append(entry_key)

        entry_val = Adw.EntryRow()
        entry_val.set_title("Value (e.g. 24, wayland)")
        box.append(entry_val)

        dialog.set_extra_child(box)

        def on_response(dlg, response_id):
            if response_id == "save":
                k = entry_key.get_text().strip()
                v = entry_val.get_text().strip()
                if k:
                    self.cfg.vars[k] = v
                    self.win.mark_modified()
                    self._populate_list()

        dialog.connect("response", on_response)
        dialog.present()
