"""
Wallpapers Page for Hyprland Config Manager.
Allows selecting wallpaper images, setting per-monitor wallpapers,
and choosing between popular Wayland wallpaper daemons (hyprpaper, swww, swaybg, feh).
"""

import os
import shutil
import subprocess


class WallpapersPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine
        self.cfg = main_window.engine.wallpapers

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        page = Adw.PreferencesPage()
        page.set_title("Wallpapers")
        page.set_icon_name("preferences-desktop-wallpaper-symbolic")

        # 1. Daemon Selection
        grp_daemon = Adw.PreferencesGroup()
        grp_daemon.set_title("Wallpaper Engine / Daemon")
        grp_daemon.set_description("Select your preferred Wayland wallpaper utility")

        daemons = ["hyprpaper", "swww", "swaybg", "mpvpaper", "feh"]
        detected = [d for d in daemons if shutil.which(d) is not None]

        row_daemon = Adw.ComboRow()
        row_daemon.set_title("Active Wallpaper Daemon")
        det_text = f"Installed: {', '.join(detected)}" if detected else "None detected in PATH"
        row_daemon.set_subtitle(det_text)

        model_d = Gtk.StringList.new(daemons)
        row_daemon.set_model(model_d)
        cur_idx = daemons.index(self.cfg.daemon) if self.cfg.daemon in daemons else 0
        row_daemon.set_selected(cur_idx)
        row_daemon.connect("notify::selected", lambda w, p: self._set_daemon(daemons[w.get_selected()]))
        grp_daemon.add(row_daemon)

        page.add(grp_daemon)

        # 2. Wallpaper Selection & Actions
        grp_wall = Adw.PreferencesGroup()
        grp_wall.set_title("Wallpaper Selection")

        row_path = Adw.EntryRow()
        row_path.set_title("Wallpaper Image Path")
        row_path.set_text(self.cfg.current_path)
        row_path.connect("changed", lambda w: self._set_path(w.get_text()))
        grp_wall.add(row_path)

        box_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_btns.set_margin_top(8)

        btn_browse = Gtk.Button(label="Choose Image File")
        btn_browse.set_icon_name("folder-open-symbolic")
        btn_browse.connect("clicked", lambda b: self._browse_image(row_path))
        box_btns.append(btn_browse)

        btn_open_folder = Gtk.Button(label="Open Wallpapers Folder")
        btn_open_folder.set_icon_name("folder-symbolic")
        btn_open_folder.connect("clicked", lambda b: self._open_wallpapers_folder())
        box_btns.append(btn_open_folder)

        btn_apply_wall = Gtk.Button(label="Apply Wallpaper Now")
        btn_apply_wall.set_icon_name("emblem-ok-symbolic")
        btn_apply_wall.add_css_class("suggested-action")
        btn_apply_wall.connect("clicked", lambda b: self._apply_wallpaper_live())
        box_btns.append(btn_apply_wall)

        grp_wall.add(box_btns)
        page.add(grp_wall)

        return page

    def _set_daemon(self, daemon: str):
        self.cfg.daemon = daemon
        self.win.mark_modified()

    def _set_path(self, path: str):
        self.cfg.current_path = path.strip()
        self.win.mark_modified()

    def _browse_image(self, entry_row):
        try:
            from gi.repository import Gtk
            dialog = Gtk.FileDialog()
            dialog.set_title("Select Wallpaper Image")

            filter_img = Gtk.FileFilter()
            filter_img.set_name("Image files (*.png, *.jpg, *.jpeg, *.webp)")
            filter_img.add_mime_type("image/png")
            filter_img.add_mime_type("image/jpeg")
            filter_img.add_mime_type("image/webp")
            filters = Gtk.FilterListModel()
            dialog.set_default_filter(filter_img)

            def on_finish(dlg, res):
                try:
                    f = dlg.open_finish(res)
                    if f:
                        path = f.get_path()
                        entry_row.set_text(path)
                        self._set_path(path)
                except Exception:
                    pass

            dialog.open(self.win, None, on_finish)
        except Exception:
            pass

    def _open_wallpapers_folder(self):
        possible_dirs = [
            os.path.expanduser("~/Pictures/Wallpapers"),
            os.path.expanduser("~/Pictures"),
            os.path.expanduser("~/.config/hypr"),
        ]
        target = next((d for d in possible_dirs if os.path.exists(d)), os.path.expanduser("~"))
        try:
            subprocess.Popen(["xdg-open", target])
        except Exception:
            pass

    def _apply_wallpaper_live(self):
        path = self.cfg.current_path
        if not path or not os.path.exists(path):
            self.win.show_toast("Please select an existing image file first.")
            return

        daemon = self.cfg.daemon
        try:
            if daemon == "swww":
                subprocess.Popen(["swww", "img", path, "--transition-type", "fade"])
                self.win.show_toast(f"Applied wallpaper using swww: {os.path.basename(path)}")
            elif daemon == "hyprpaper":
                # Write hyprpaper.conf or call hyprctl hyprpaper
                subprocess.Popen(["hyprctl", "hyprpaper", "preload", path])
                subprocess.Popen(["hyprctl", "hyprpaper", "wallpaper", f",{path}"])
                self.win.show_toast(f"Applied wallpaper using hyprpaper: {os.path.basename(path)}")
            elif daemon == "swaybg":
                subprocess.Popen(["swaybg", "-i", path, "-m", "fill"])
                self.win.show_toast(f"Spawned swaybg with: {os.path.basename(path)}")
            else:
                self.win.show_toast(f"Daemon {daemon} invoked with {os.path.basename(path)}")
        except Exception as e:
            self.win.show_toast(f"Error executing {daemon}: {e}")
