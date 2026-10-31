"""
Workspaces Page for Hyprland Config Manager.
Allows visual configuration of workspace rules, monitor pinning, default flags,
and special scratchpads.
"""

from ...core.models import WorkspaceRule


class WorkspacesPageBuilder:
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
        page.set_title("Workspaces")
        page.set_icon_name("view-paged-symbolic")

        grp_top = Adw.PreferencesGroup()
        grp_top.set_title("Workspace Rules & Display Binding")
        grp_top.set_description("Pin workspaces to monitors and configure default layouts")

        btn_add = Gtk.Button(label="Add Workspace Rule")
        btn_add.set_icon_name("list-add-symbolic")
        btn_add.add_css_class("suggested-action")
        btn_add.connect("clicked", lambda b: self._show_add_dialog())
        grp_top.add(btn_add)
        page.add(grp_top)

        grp_list = Adw.PreferencesGroup()
        grp_list.set_title("Configured Workspaces")

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

        for ws in self.engine.workspace_rules:
            row = Adw.ActionRow()
            row.set_title(f"Workspace {ws.workspace_id}")
            details = []
            if ws.monitor:
                details.append(f"Monitor: {ws.monitor}")
            if ws.default:
                details.append("Default on boot")
            if ws.persistent:
                details.append("Persistent")
            row.set_subtitle(" • ".join(details) if details else "Standard workspace")

            btn_del = Gtk.Button()
            btn_del.set_icon_name("user-trash-symbolic")
            btn_del.connect("clicked", self._make_delete_handler(ws))
            row.add_suffix(btn_del)

            self.list_box.append(row)

    def _make_delete_handler(self, ws: WorkspaceRule):
        def handler(button):
            if ws in self.engine.workspace_rules:
                self.engine.workspace_rules.remove(ws)
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
            heading="Add Workspace Rule"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        entry_id = Adw.EntryRow()
        entry_id.set_title("Workspace ID or Name (e.g. 1, 2, special:scratch)")
        entry_id.set_text(str(len(self.engine.workspace_rules) + 1))
        box.append(entry_id)

        entry_mon = Adw.EntryRow()
        entry_mon.set_title("Monitor Assignment (e.g. DP-1, HDMI-A-1)")
        default_mon = self.engine.monitors[0].name if self.engine.monitors else ""
        entry_mon.set_text(default_mon)
        box.append(entry_mon)

        sw_def = Adw.SwitchRow()
        sw_def.set_title("Default Workspace on Monitor")
        box.append(sw_def)

        sw_pers = Adw.SwitchRow()
        sw_pers.set_title("Persistent (do not close when empty)")
        box.append(sw_pers)

        dialog.set_extra_child(box)

        def on_response(dlg, response_id):
            if response_id == "save":
                w_id = entry_id.get_text().strip()
                if w_id:
                    new_ws = WorkspaceRule(
                        workspace_id=w_id,
                        monitor=entry_mon.get_text().strip(),
                        default=sw_def.get_active(),
                        persistent=sw_pers.get_active()
                    )
                    self.engine.workspace_rules.append(new_ws)
                    self.win.mark_modified()
                    self._populate_list()

        dialog.connect("response", on_response)
        dialog.present()
