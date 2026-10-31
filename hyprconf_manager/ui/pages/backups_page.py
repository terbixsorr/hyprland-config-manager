"""
Backup History Page for Hyprland Config Manager.
Allows browsing past configuration snapshots, inspecting diffs, restoring,
and deleting backups.
"""

from ...core.generator import HyprlandGenerator


class BackupsPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.backup_mgr = main_window.backup_mgr
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
        page.set_title("Backups")
        page.set_icon_name("document-revert-symbolic")

        grp_top = Adw.PreferencesGroup()
        grp_top.set_title("Backup History & Snapshots")
        grp_top.set_description("Automatic backups captured before applies, profile changes, and manual snapshots")

        btn_snap = Gtk.Button(label="Create Manual Snapshot")
        btn_snap.set_icon_name("document-save-symbolic")
        btn_snap.add_css_class("suggested-action")
        btn_snap.connect("clicked", lambda b: self._create_manual_snapshot())
        grp_top.add(btn_snap)
        page.add(grp_top)

        grp_list = Adw.PreferencesGroup()
        grp_list.set_title("Available Snapshots")

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

        backups = self.backup_mgr.list_backups()
        if not backups:
            row_empty = Adw.ActionRow()
            row_empty.set_title("No backups recorded yet")
            row_empty.set_subtitle("Snapshots are automatically created before applying configuration changes.")
            self.list_box.append(row_empty)
            return

        for b in backups:
            row = Adw.ActionRow()
            row.set_title(b.timestamp)
            row.set_subtitle(f"{b.reason} ({b.size_bytes} bytes)")

            # Diff button
            btn_diff = Gtk.Button(label="Diff")
            btn_diff.set_icon_name("document-properties-symbolic")
            btn_diff.connect("clicked", self._make_diff_handler(b))
            row.add_suffix(btn_diff)

            # Restore button
            btn_restore = Gtk.Button(label="Restore")
            btn_restore.set_icon_name("edit-undo-symbolic")
            btn_restore.connect("clicked", self._make_restore_handler(b))
            row.add_suffix(btn_restore)

            # Delete button
            btn_del = Gtk.Button()
            btn_del.set_icon_name("user-trash-symbolic")
            btn_del.connect("clicked", self._make_delete_handler(b))
            row.add_suffix(btn_del)

            self.list_box.append(row)

    def _create_manual_snapshot(self):
        curr_text = self.engine.generate_candidate_config()
        entry = self.backup_mgr.create_backup(curr_text, reason="Manual user snapshot")
        self._populate_list()
        self.win.show_toast(f"Snapshot created: {entry.timestamp}")

    def _make_restore_handler(self, backup_entry):
        def handler(button):
            ok, msg = self.win.safe_apply.rollback(self.engine, backup_id=backup_entry.id)
            if ok:
                self.win.show_toast(f"Restored backup from {backup_entry.timestamp}")
                self.win.refresh_all_pages()
            else:
                self.win.show_toast(f"Restore failed: {msg}")
        return handler

    def _make_delete_handler(self, backup_entry):
        def handler(button):
            self.backup_mgr.delete_backup(backup_entry.id)
            self._populate_list()
            self.win.show_toast("Backup removed")
        return handler

    def _make_diff_handler(self, backup_entry):
        def handler(button):
            old_content = self.backup_mgr.get_backup_content(backup_entry.id) or ""
            current_content = self.engine.generate_candidate_config()
            diff_text = HyprlandGenerator.compute_diff(
                old_content,
                current_content,
                old_label=f"Backup ({backup_entry.timestamp})",
                new_label="Current GUI Draft"
            )
            self.win.show_diff_dialog(diff_text or "No differences found between snapshot and current configuration.")
        return handler
