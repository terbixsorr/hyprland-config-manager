"""
Startup Applications Page for Hyprland Config Manager.
Allows managing exec-once and exec autostart daemons and applications.
"""

from ...core.models import StartupItem


class StartupPageBuilder:
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
        page.set_title("Startup")
        page.set_icon_name("system-run-symbolic")

        grp_top = Adw.PreferencesGroup()
        grp_top.set_title("Autostart Applications")
        grp_top.set_description("Programs and background services executed when Hyprland launches")

        btn_add = Gtk.Button(label="Add Startup Application")
        btn_add.set_icon_name("list-add-symbolic")
        btn_add.add_css_class("suggested-action")
        btn_add.connect("clicked", lambda b: self._show_add_dialog())
        grp_top.add(btn_add)
        page.add(grp_top)

        grp_list = Adw.PreferencesGroup()
        grp_list.set_title("Configured Startup Items")

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

        for item in self.engine.startup_items:
            row = Adw.ActionRow()
            row.set_title(item.command)
            row.set_subtitle(f"Type: {item.exec_type}")

            # Enable/Disable switch
            sw = Gtk.Switch()
            sw.set_active(item.enabled)
            sw.connect("notify::active", self._make_toggle_handler(item))
            row.add_suffix(sw)

            # Edit button
            btn_edit = Gtk.Button()
            btn_edit.set_icon_name("document-edit-symbolic")
            btn_edit.connect("clicked", self._make_edit_handler(item))
            row.add_suffix(btn_edit)

            # Delete button
            btn_del = Gtk.Button()
            btn_del.set_icon_name("user-trash-symbolic")
            btn_del.connect("clicked", self._make_delete_handler(item))
            row.add_suffix(btn_del)

            self.list_box.append(row)

    def _make_toggle_handler(self, item: StartupItem):
        def handler(widget, param):
            item.enabled = widget.get_active()
            self.win.mark_modified()
        return handler

    def _make_delete_handler(self, item: StartupItem):
        def handler(button):
            if item in self.engine.startup_items:
                self.engine.startup_items.remove(item)
                self.win.mark_modified()
                self._populate_list()
        return handler

    def _make_edit_handler(self, item: StartupItem):
        def handler(button):
            self._show_edit_dialog(item)
        return handler

    def _show_add_dialog(self):
        new_item = StartupItem(command="", exec_type="exec-once", enabled=True)
        self._show_edit_dialog(new_item, is_new=True)

    def _show_edit_dialog(self, item: StartupItem, is_new: bool = False):
        try:
            from gi.repository import Gtk, Adw
        except ImportError:
            return

        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Edit Startup Command" if not is_new else "Add Startup Command"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        entry_cmd = Adw.EntryRow()
        entry_cmd.set_title("Command to Execute")
        entry_cmd.set_text(item.command)
        box.append(entry_cmd)

        row_type = Adw.ComboRow()
        row_type.set_title("Execution Mode")
        model = Gtk.StringList.new(["exec-once (runs on Hyprland startup)", "exec (runs on every reload)"])
        row_type.set_model(model)
        row_type.set_selected(0 if item.exec_type == "exec-once" else 1)
        box.append(row_type)

        dialog.set_extra_child(box)

        def on_response(dlg, response_id):
            if response_id == "save":
                cmd = entry_cmd.get_text().strip()
                if cmd:
                    item.command = cmd
                    item.exec_type = "exec-once" if row_type.get_selected() == 0 else "exec"
                    if is_new:
                        self.engine.startup_items.append(item)
                    self.win.mark_modified()
                    self._populate_list()

        dialog.connect("response", on_response)
        dialog.present()
