"""
Animations Configuration Page for Hyprland Config Manager.
Allows configuring Bezier curves, animation targets (windows, fade, border, workspaces),
and applying curated speed/feel presets (Minimal, Smooth, Fast, Gaming, Custom).
"""

from ...core.models import ANIMATION_PRESETS


class AnimationsPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine
        self.cfg = main_window.engine.animations

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        page = Adw.PreferencesPage()
        page.set_title("Animations")
        page.set_icon_name("media-playback-start-symbolic")

        # 1. Master Animation Toggle & Presets
        grp_master = Adw.PreferencesGroup()
        grp_master.set_title("Master Animation Settings")
        grp_master.set_description("Compositor motion curve engine and global presets")

        row_enable = Adw.SwitchRow()
        row_enable.set_title("Enable Animations")
        row_enable.set_active(self.cfg.enabled)
        row_enable.connect("notify::active", lambda w, p: self._set_enabled(w.get_active()))
        grp_master.add(row_enable)

        row_preset = Adw.ComboRow()
        row_preset.set_title("Animation Preset")
        presets = ["Smooth", "Minimal", "Fast", "Gaming", "Custom"]
        model_presets = Gtk.StringList.new(presets)
        row_preset.set_model(model_presets)

        cur_idx = presets.index(self.cfg.preset) if self.cfg.preset in presets else len(presets) - 1
        row_preset.set_selected(cur_idx)
        grp_master.add(row_preset)

        page.add(grp_master)

        # 2. Animation Targets (Windows, Workspaces, Fade, Border)
        grp_targets = Adw.PreferencesGroup()
        grp_targets.set_title("Animation Targets & Speeds")

        targets_info = [
            ("windows", "Window Open / Spawn"),
            ("windowsOut", "Window Close / Exit"),
            ("workspaces", "Workspace Switch"),
            ("fade", "Fade / Opacity Transitions"),
            ("border", "Window Border Color Shift"),
        ]

        spin_rows = {}
        switch_rows = {}

        for target_key, target_title in targets_info:
            target_data = self.cfg.animations.get(target_key, {"enabled": True, "speed": 6, "curve": "default"})

            row_target = Adw.ActionRow()
            row_target.set_title(target_title)

            # Target enable switch
            sw = Gtk.Switch()
            sw.set_active(target_data.get("enabled", True))
            sw.connect("notify::active", self._make_target_switch_handler(target_key))
            switch_rows[target_key] = sw
            row_target.add_suffix(sw)

            # Speed spin button
            spin = Gtk.SpinButton.new_with_range(1, 20, 1)
            spin.set_value(target_data.get("speed", 6))
            spin.connect("value-changed", self._make_target_speed_handler(target_key))
            spin_rows[target_key] = spin
            row_target.add_suffix(spin)

            grp_targets.add(row_target)

        page.add(grp_targets)

        # 3. Bezier Curves Group
        grp_beziers = Adw.PreferencesGroup()
        grp_beziers.set_title("Cubic Bezier Curves")
        grp_beziers.set_description("Four-point control coordinates (x1, y1, x2, y2)")

        for b_name, b_coords in self.cfg.bezier_curves.items():
            row_b = Adw.EntryRow()
            row_b.set_title(b_name)
            row_b.set_text(b_coords)
            row_b.connect("changed", self._make_bezier_handler(b_name))
            grp_beziers.add(row_b)

        page.add(grp_beziers)

        # Wire preset change listener
        def on_preset_changed(widget, param):
            p_name = presets[widget.get_selected()]
            self.cfg.preset = p_name
            if p_name in ANIMATION_PRESETS:
                p_data = ANIMATION_PRESETS[p_name]
                self.cfg.enabled = p_data["enabled"]
                row_enable.set_active(self.cfg.enabled)

                for t_key, t_settings in p_data["animations"].items():
                    if t_key in self.cfg.animations:
                        self.cfg.animations[t_key].update(t_settings)
                    else:
                        self.cfg.animations[t_key] = t_settings

                    if t_key in switch_rows:
                        switch_rows[t_key].set_active(t_settings.get("enabled", True))
                    if t_key in spin_rows:
                        spin_rows[t_key].set_value(t_settings.get("speed", 6))

            self.win.mark_modified()

        row_preset.connect("notify::selected", on_preset_changed)

        return page

    def _set_enabled(self, val: bool):
        self.cfg.enabled = val
        self.win.mark_modified()

    def _make_target_switch_handler(self, target_key: str):
        def handler(widget, param):
            if target_key not in self.cfg.animations:
                self.cfg.animations[target_key] = {}
            self.cfg.animations[target_key]["enabled"] = widget.get_active()
            self.cfg.preset = "Custom"
            self.win.mark_modified()
        return handler

    def _make_target_speed_handler(self, target_key: str):
        def handler(widget):
            if target_key not in self.cfg.animations:
                self.cfg.animations[target_key] = {}
            self.cfg.animations[target_key]["speed"] = int(widget.get_value())
            self.cfg.preset = "Custom"
            self.win.mark_modified()
        return handler

    def _make_bezier_handler(self, b_name: str):
        def handler(widget):
            self.cfg.bezier_curves[b_name] = widget.get_text().strip()
            self.win.mark_modified()
        return handler
