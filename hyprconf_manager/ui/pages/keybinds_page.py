"""
Keybindings Management Page for Hyprland Config Manager.
Allows searching, adding, editing, and deleting keybindings with real-time conflict detection.
"""

from ...core.models import KeybindItem


class KeybindsPageBuilder:
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
        page.set_title("Keybinds")
        page.set_icon_name("input-keyboard-symbolic")

        # 1. Search & Actions Group
        grp_top = Adw.PreferencesGroup()
        grp_top.set_title("Keybindings Management")
        grp_top.set_description("Manage compositor shortcuts, application launches, and window management")

        box_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # Search Entry
        search_entry = Gtk.SearchEntry()
        search_entry.set_hexpand(True)
        search_entry.set_placeholder_text("Search keybindings (e.g. SUPER, kitty, workspace, exec)...")
        box_top.append(search_entry)

        # [Add Binding] Button
        btn_add = Gtk.Button(label="Add Keybind")
        btn_add.set_icon_name("list-add-symbolic")
        btn_add.add_css_class("suggested-action")
        btn_add.connect("clicked", lambda b: self._show_add_dialog())
        box_top.append(btn_add)

        grp_top.add(box_top)
        page.add(grp_top)

        # Conflict Banner
        conflicts = self._detect_conflicts()
        if conflicts:
            grp_warn = Adw.PreferencesGroup()
            banner = Adw.Banner()
            banner.set_title(f"⚠️ Warning: {len(conflicts)} duplicate keybinding(s) detected: {', '.join(conflicts[:3])}")
            banner.set_revealed(True)
            grp_warn.add(banner)
            page.add(grp_warn)

        # 2. Keybindings Table / List Group
        grp_list = Adw.PreferencesGroup()
        grp_list.set_title("Configured Keybindings")

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")

        self._populate_list(self.engine.keybinds)

        # Connect search filter
        def on_search_changed(entry):
            query = entry.get_text().strip().lower()
            if not query:
                self._populate_list(self.engine.keybinds)
                return
            filtered = [
                kb for kb in self.engine.keybinds
                if query in kb.modifier.lower() or query in kb.key.lower()
                or query in kb.dispatcher.lower() or query in kb.arguments.lower()
            ]
            self._populate_list(filtered)

        search_entry.connect("search-changed", on_search_changed)

        grp_list.add(self.list_box)
        page.add(grp_list)

        return page

    def _detect_conflicts(self):
        seen = {}
        conflicts = []
        for kb in self.engine.keybinds:
            combo = kb.get_full_combination().lower()
            if combo in seen:
                conflicts.append(kb.get_full_combination())
            else:
                seen[combo] = True
        return conflicts

    def _populate_list(self, keybinds):
        try:
            from gi.repository import Gtk, Adw
        except ImportError:
            return

        # Clear existing children
        while True:
            child = self.list_box.get_first_child()
            if not child:
                break
            self.list_box.remove(child)

        for kb in keybinds:
            row = Adw.ActionRow()
            row.set_title(kb.get_full_combination())
            arg_str = f" → {kb.arguments}" if kb.arguments else ""
            row.set_subtitle(f"Action: {kb.dispatcher}{arg_str}")

            # Edit button
            btn_edit = Gtk.Button()
            btn_edit.set_icon_name("document-edit-symbolic")
            btn_edit.connect("clicked", self._make_edit_handler(kb))
            row.add_suffix(btn_edit)

            # Delete button
            btn_del = Gtk.Button()
            btn_del.set_icon_name("user-trash-symbolic")
            btn_del.connect("clicked", self._make_delete_handler(kb))
            row.add_suffix(btn_del)

            self.list_box.append(row)

    def _make_delete_handler(self, kb: KeybindItem):
        def handler(button):
            if kb in self.engine.keybinds:
                self.engine.keybinds.remove(kb)
                self.win.mark_modified()
                self._populate_list(self.engine.keybinds)
        return handler

    def _make_edit_handler(self, kb: KeybindItem):
        def handler(button):
            self._show_edit_dialog(kb)
        return handler

    def _show_add_dialog(self):
        new_kb = KeybindItem(modifier="SUPER", key="", dispatcher="exec", arguments="")
        self._show_edit_dialog(new_kb, is_new=True)

    def _show_edit_dialog(self, kb: KeybindItem, is_new: bool = False):
        try:
            from gi.repository import Gtk, Adw
        except ImportError:
            return

        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Edit Keybinding" if not is_new else "Add New Keybinding"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        entry_mod = Adw.EntryRow()
        entry_mod.set_title("Modifier (e.g. SUPER, SUPER_SHIFT, CTRL)")
        entry_mod.set_text(kb.modifier)
        box.append(entry_mod)

        entry_key = Adw.EntryRow()
        entry_key.set_title("Key (e.g. Q, Return, Space, 1)")
        entry_key.set_text(kb.key)
        box.append(entry_key)

        entry_disp = Adw.EntryRow()
        entry_disp.set_title("Dispatcher (e.g. exec, killactive, workspace)")
        entry_disp.set_text(kb.dispatcher)
        box.append(entry_disp)

        entry_args = Adw.EntryRow()
        entry_args.set_title("Arguments (e.g. kitty, 1, togglefloating)")
        entry_args.set_text(kb.arguments)
        box.append(entry_args)

        dialog.set_extra_child(box)

        def on_response(dlg, response_id):
            if response_id == "save":
                kb.modifier = entry_mod.get_text().strip()
                kb.key = entry_key.get_text().strip()
                kb.dispatcher = entry_disp.get_text().strip()
                kb.arguments = entry_args.get_text().strip()
                if is_new and kb.key:
                    self.engine.keybinds.append(kb)
                self.win.mark_modified()
                self._populate_list(self.engine.keybinds)

        dialog.connect("response", on_response)
        dialog.present()
