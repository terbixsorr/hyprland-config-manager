"""
Windows & Decoration Page for Hyprland Config Manager.
Allows fine-tuning window layout, gaps, borders, opacities, shadows, and blur.
"""


class WindowsPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine
        self.cfg = main_window.engine.windows

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        page = Adw.PreferencesPage()
        page.set_title("Windows")
        page.set_icon_name("preferences-desktop-windows-symbolic")

        # 1. Geometry & Gaps
        grp_geo = Adw.PreferencesGroup()
        grp_geo.set_title("Geometry & Gaps")
        grp_geo.set_description("Spacing, border widths, and layout engine")

        # Layout selector
        row_layout = Adw.ComboRow()
        row_layout.set_title("Window Tiling Layout")
        model_layout = Gtk.StringList.new(["dwindle", "master"])
        row_layout.set_model(model_layout)
        row_layout.set_selected(1 if self.cfg.layout == "master" else 0)
        row_layout.connect("notify::selected", lambda w, p: self._set_layout(model_layout.get_string(w.get_selected())))
        grp_geo.add(row_layout)

        # Border size
        row_border = Adw.SpinRow.new_with_range(0, 15, 1)
        row_border.set_title("Border Width (px)")
        row_border.set_value(self.cfg.border_size)
        row_border.connect("notify::value", lambda w, p: self._set_val("border_size", int(w.get_value())))
        grp_geo.add(row_border)

        # Rounding (Border radius)
        row_rounding = Adw.SpinRow.new_with_range(0, 35, 1)
        row_rounding.set_title("Window Corner Radius (px)")
        row_rounding.set_value(self.cfg.rounding)
        row_rounding.connect("notify::value", lambda w, p: self._set_val("rounding", int(w.get_value())))
        grp_geo.add(row_rounding)

        # Gaps In
        row_gaps_in = Adw.SpinRow.new_with_range(0, 60, 1)
        row_gaps_in.set_title("Inner Gaps (between windows, px)")
        row_gaps_in.set_value(self.cfg.gaps_in)
        row_gaps_in.connect("notify::value", lambda w, p: self._set_val("gaps_in", int(w.get_value())))
        grp_geo.add(row_gaps_in)

        # Gaps Out
        row_gaps_out = Adw.SpinRow.new_with_range(0, 80, 1)
        row_gaps_out.set_title("Outer Gaps (screen edges, px)")
        row_gaps_out.set_value(self.cfg.gaps_out)
        row_gaps_out.connect("notify::value", lambda w, p: self._set_val("gaps_out", int(w.get_value())))
        grp_geo.add(row_gaps_out)

        page.add(grp_geo)

        # 2. Window Opacity & Focus Behavior
        grp_op = Adw.PreferencesGroup()
        grp_op.set_title("Opacity & Focus Behavior")

        # Active Opacity
        row_act_op = Adw.SpinRow.new_with_range(0.2, 1.0, 0.05)
        row_act_op.set_title("Active Window Opacity")
        row_act_op.set_value(self.cfg.active_opacity)
        row_act_op.connect("notify::value", lambda w, p: self._set_val("active_opacity", float(w.get_value())))
        grp_op.add(row_act_op)

        # Inactive Opacity
        row_inact_op = Adw.SpinRow.new_with_range(0.2, 1.0, 0.05)
        row_inact_op.set_title("Inactive Window Opacity")
        row_inact_op.set_value(self.cfg.inactive_opacity)
        row_inact_op.connect("notify::value", lambda w, p: self._set_val("inactive_opacity", float(w.get_value())))
        grp_op.add(row_inact_op)

        # Follow Mouse
        row_fm = Adw.ComboRow()
        row_fm.set_title("Focus Follows Mouse")
        model_fm = Gtk.StringList.new(["Disabled (0)", "Enabled (1)", "Loose (2)", "Strict (3)"])
        row_fm.set_model(model_fm)
        row_fm.set_selected(self.cfg.follow_mouse if 0 <= self.cfg.follow_mouse <= 3 else 1)
        row_fm.connect("notify::selected", lambda w, p: self._set_val("follow_mouse", w.get_selected()))
        grp_op.add(row_fm)

        page.add(grp_op)

        # 3. Shadows & Blur
        grp_fx = Adw.PreferencesGroup()
        grp_fx.set_title("Shadows & Blur Effects")

        # Drop Shadow
        row_shadow = Adw.SwitchRow()
        row_shadow.set_title("Enable Drop Shadows")
        row_shadow.set_active(self.cfg.drop_shadow)
        row_shadow.connect("notify::active", lambda w, p: self._set_val("drop_shadow", w.get_active()))
        grp_fx.add(row_shadow)

        # Shadow Range
        row_sr = Adw.SpinRow.new_with_range(1, 60, 1)
        row_sr.set_title("Shadow Range (px)")
        row_sr.set_value(self.cfg.shadow_range)
        row_sr.connect("notify::value", lambda w, p: self._set_val("shadow_range", int(w.get_value())))
        grp_fx.add(row_sr)

        # Blur Enabled
        row_blur = Adw.SwitchRow()
        row_blur.set_title("Enable Window Blur (Dual-Kawase)")
        row_blur.set_active(self.cfg.blur_enabled)
        row_blur.connect("notify::active", lambda w, p: self._set_val("blur_enabled", w.get_active()))
        grp_fx.add(row_blur)

        # Blur Size
        row_bs = Adw.SpinRow.new_with_range(1, 25, 1)
        row_bs.set_title("Blur Radius / Size")
        row_bs.set_value(self.cfg.blur_size)
        row_bs.connect("notify::value", lambda w, p: self._set_val("blur_size", int(w.get_value())))
        grp_fx.add(row_bs)

        # Blur Passes
        row_bp = Adw.SpinRow.new_with_range(1, 8, 1)
        row_bp.set_title("Blur Passes")
        row_bp.set_value(self.cfg.blur_passes)
        row_bp.connect("notify::value", lambda w, p: self._set_val("blur_passes", int(w.get_value())))
        grp_fx.add(row_bp)

        page.add(grp_fx)

        return page

    def _set_layout(self, val: str):
        self.cfg.layout = val
        self.win.mark_modified()

    def _set_val(self, prop: str, val):
        setattr(self.cfg, prop, val)
        self.win.mark_modified()
