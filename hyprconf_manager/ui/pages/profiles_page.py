"""
Profiles Management Page for Hyprland Config Manager.
Allows creating, duplicating, renaming, exporting, importing, and activating
curated profiles (Gaming, Work, Laptop, Minimal, Streaming) with auto-backup.
"""


class ProfilesPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.profile_mgr = main_window.profile_mgr
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
        page.set_title("Profiles")
        page.set_icon_name("starred-symbolic")

        # 1. Action Header Group
        grp_top = Adw.PreferencesGroup()
        grp_top.set_title("Configuration Profiles")
        grp_top.set_description("Switch between dedicated workflows (Gaming, Work, Laptop, Minimal, Streaming)")

        box_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        btn_new = Gtk.Button(label="Create Profile")
        btn_new.set_icon_name("document-new-symbolic")
        btn_new.add_css_class("suggested-action")
        btn_new.connect("clicked", lambda b: self._show_create_dialog())
        box_top.append(btn_new)

        btn_import = Gtk.Button(label="Import Profile")
        btn_import.set_icon_name("document-open-symbolic")
        btn_import.connect("clicked", lambda b: self._import_profile())
        box_top.append(btn_import)

        grp_top.add(box_top)
        page.add(grp_top)

        # 2. Profiles List Group
        grp_list = Adw.PreferencesGroup()
        grp_list.set_title("Saved Profiles")

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

        active_prof = self.profile_mgr.get_active_profile()

        for prof_name in self.profile_mgr.list_profiles():
            prof_data = self.profile_mgr.load_profile(prof_name) or {}
            desc = prof_data.get("description", "User configuration profile")

            row = Adw.ActionRow()
            row.set_title(prof_name)
            row.set_subtitle(desc)

            if prof_name == active_prof:
                badge = Gtk.Label(label="ACTIVE")
                badge.add_css_class("status-dot-active")
                row.add_suffix(badge)
            else:
                btn_activate = Gtk.Button(label="Activate")
                btn_activate.set_icon_name("emblem-ok-symbolic")
                btn_activate.connect("clicked", self._make_activate_handler(prof_name))
                row.add_suffix(btn_activate)

            # Duplicate button
            btn_dup = Gtk.Button()
            btn_dup.set_icon_name("edit-copy-symbolic")
            btn_dup.set_tooltip_text("Duplicate Profile")
            btn_dup.connect("clicked", self._make_duplicate_handler(prof_name))
            row.add_suffix(btn_dup)

            # Export button
            btn_exp = Gtk.Button()
            btn_exp.set_icon_name("document-save-as-symbolic")
            btn_exp.set_tooltip_text("Export to JSON")
            btn_exp.connect("clicked", self._make_export_handler(prof_name))
            row.add_suffix(btn_exp)

            # Delete button
            if prof_name != "Work":  # Protect base profile
                btn_del = Gtk.Button()
                btn_del.set_icon_name("user-trash-symbolic")
                btn_del.set_tooltip_text("Delete Profile")
                btn_del.connect("clicked", self._make_delete_handler(prof_name))
                row.add_suffix(btn_del)

            self.list_box.append(row)

    def _make_activate_handler(self, name: str):
        def handler(button):
            self.win.activate_profile(name)
            self._populate_list()
        return handler

    def _make_duplicate_handler(self, name: str):
        def handler(button):
            new_name = f"{name}_Copy"
            self.profile_mgr.duplicate_profile(name, new_name)
            self._populate_list()
            self.win.show_toast(f"Duplicated profile to '{new_name}'")
        return handler

    def _make_delete_handler(self, name: str):
        def handler(button):
            self.profile_mgr.delete_profile(name)
            self._populate_list()
            self.win.show_toast(f"Deleted profile '{name}'")
        return handler

    def _make_export_handler(self, name: str):
        def handler(button):
            try:
                from gi.repository import Gtk
                dialog = Gtk.FileDialog()
                dialog.set_title(f"Export Profile '{name}'")
                dialog.set_initial_name(f"{name}.json")

                def on_finish(dlg, res):
                    try:
                        f = dlg.save_finish(res)
                        if f:
                            path = f.get_path()
                            ok, msg = self.profile_mgr.export_profile(name, path)
                            self.win.show_toast(msg)
                    except Exception as e:
                        self.win.show_toast(f"Export failed: {e}")

                dialog.save(self.win, None, on_finish)
            except Exception:
                pass
        return handler

    def _import_profile(self):
        try:
            from gi.repository import Gtk
            dialog = Gtk.FileDialog()
            dialog.set_title("Import Profile JSON")

            def on_finish(dlg, res):
                try:
                    f = dlg.open_finish(res)
                    if f:
                        path = f.get_path()
                        ok, imported_name = self.profile_mgr.import_profile(path)
                        if ok:
                            self._populate_list()
                            self.win.show_toast(f"Successfully imported profile: {imported_name}")
                        else:
                            self.win.show_toast(f"Failed to import: {imported_name}")
                except Exception as e:
                    self.win.show_toast(f"Import error: {e}")

            dialog.open(self.win, None, on_finish)
        except Exception:
            pass

    def _show_create_dialog(self):
        try:
            from gi.repository import Gtk, Adw
        except ImportError:
            return

        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Create New Profile"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Create")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        entry_name = Adw.EntryRow()
        entry_name.set_title("Profile Name")
        box.append(entry_name)

        entry_desc = Adw.EntryRow()
        entry_desc.set_title("Description")
        box.append(entry_desc)

        dialog.set_extra_child(box)

        def on_response(dlg, response_id):
            if response_id == "save":
                p_name = entry_name.get_text().strip()
                if p_name:
                    p_data = {
                        "description": entry_desc.get_text().strip(),
                        "windows": {
                            "border_size": self.engine.windows.border_size,
                            "rounding": self.engine.windows.rounding,
                            "gaps_in": self.engine.windows.gaps_in,
                            "gaps_out": self.engine.windows.gaps_out,
                            "active_opacity": self.engine.windows.active_opacity,
                            "inactive_opacity": self.engine.windows.inactive_opacity,
                        },
                        "animations": {
                            "enabled": self.engine.animations.enabled,
                            "preset": self.engine.animations.preset
                        },
                        "appearance": {
                            "theme_name": self.engine.appearance.theme_name
                        }
                    }
                    self.profile_mgr.save_profile(p_name, p_data)
                    self._populate_list()
                    self.win.show_toast(f"Created profile '{p_name}'")

        dialog.connect("response", on_response)
        dialog.present()
