"""
Input Devices Page for Hyprland Config Manager.
Allows configuration for Mouse, Keyboard, and Touchpad gestures and behavior.
"""


class InputPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine
        self.cfg = main_window.engine.input_cfg

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        page = Adw.PreferencesPage()
        page.set_title("Input")
        page.set_icon_name("input-keyboard-symbolic")

        # 1. Mouse Group
        grp_mouse = Adw.PreferencesGroup()
        grp_mouse.set_title("Mouse & Pointer")

        # Sensitivity (-1.0 to 1.0)
        row_sens = Adw.SpinRow.new_with_range(-1.0, 1.0, 0.1)
        row_sens.set_title("Pointer Sensitivity")
        row_sens.set_subtitle("-1.0 (slowest) to 1.0 (fastest), 0 is default")
        row_sens.set_value(self.cfg.mouse_sensitivity)
        row_sens.connect("notify::value", lambda w, p: self._set_val("mouse_sensitivity", float(w.get_value())))
        grp_mouse.add(row_sens)

        # Accel profile
        row_accel = Adw.ComboRow()
        row_accel.set_title("Acceleration Profile")
        accels = ["adaptive", "flat", "custom"]
        model_accel = Gtk.StringList.new(accels)
        row_accel.set_model(model_accel)
        accel_idx = accels.index(self.cfg.accel_profile) if self.cfg.accel_profile in accels else 0
        row_accel.set_selected(accel_idx)
        row_accel.connect("notify::selected", lambda w, p: self._set_val("accel_profile", accels[w.get_selected()]))
        grp_mouse.add(row_accel)

        # Natural scroll
        row_nat_scroll = Adw.SwitchRow()
        row_nat_scroll.set_title("Natural Scrolling (Mouse)")
        row_nat_scroll.set_active(self.cfg.natural_scroll)
        row_nat_scroll.connect("notify::active", lambda w, p: self._set_val("natural_scroll", w.get_active()))
        grp_mouse.add(row_nat_scroll)

        page.add(grp_mouse)

        # 2. Keyboard Group
        grp_kb = Adw.PreferencesGroup()
        grp_kb.set_title("Keyboard")

        # Layout
        row_layout = Adw.EntryRow()
        row_layout.set_title("Layout(s)")
        row_layout.set_text(self.cfg.kb_layout)
        row_layout.connect("changed", lambda w: self._set_val("kb_layout", w.get_text()))
        grp_kb.add(row_layout)

        # Options
        row_opts = Adw.EntryRow()
        row_opts.set_title("XKB Options")
        row_opts.set_text(self.cfg.kb_options)
        row_opts.connect("changed", lambda w: self._set_val("kb_options", w.get_text()))
        grp_kb.add(row_opts)

        # Repeat Rate
        row_rep_rate = Adw.SpinRow.new_with_range(10, 100, 5)
        row_rep_rate.set_title("Repeat Rate (Hz)")
        row_rep_rate.set_value(self.cfg.repeat_rate)
        row_rep_rate.connect("notify::value", lambda w, p: self._set_val("repeat_rate", int(w.get_value())))
        grp_kb.add(row_rep_rate)

        # Repeat Delay
        row_rep_del = Adw.SpinRow.new_with_range(100, 1000, 25)
        row_rep_del.set_title("Repeat Delay (ms)")
        row_rep_del.set_value(self.cfg.repeat_delay)
        row_rep_del.connect("notify::value", lambda w, p: self._set_val("repeat_delay", int(w.get_value())))
        grp_kb.add(row_rep_del)

        # Numlock by default
        row_numlock = Adw.SwitchRow()
        row_numlock.set_title("NumLock by Default")
        row_numlock.set_active(self.cfg.numlock_by_default)
        row_numlock.connect("notify::active", lambda w, p: self._set_val("numlock_by_default", w.get_active()))
        grp_kb.add(row_numlock)

        page.add(grp_kb)

        # 3. Touchpad Group
        grp_touch = Adw.PreferencesGroup()
        grp_touch.set_title("Touchpad")

        row_tp_nat = Adw.SwitchRow()
        row_tp_nat.set_title("Natural Scrolling (Touchpad)")
        row_tp_nat.set_active(self.cfg.touchpad_natural_scroll)
        row_tp_nat.connect("notify::active", lambda w, p: self._set_val("touchpad_natural_scroll", w.get_active()))
        grp_touch.add(row_tp_nat)

        row_tp_tap = Adw.SwitchRow()
        row_tp_tap.set_title("Tap to Click")
        row_tp_tap.set_active(self.cfg.touchpad_tap_to_click)
        row_tp_tap.connect("notify::active", lambda w, p: self._set_val("touchpad_tap_to_click", w.get_active()))
        grp_touch.add(row_tp_tap)

        row_tp_drag = Adw.SwitchRow()
        row_tp_drag.set_title("Tap and Drag Lock")
        row_tp_drag.set_active(self.cfg.touchpad_drag_lock)
        row_tp_drag.connect("notify::active", lambda w, p: self._set_val("touchpad_drag_lock", w.get_active()))
        grp_touch.add(row_tp_drag)

        row_tp_type = Adw.SwitchRow()
        row_tp_type.set_title("Disable While Typing")
        row_tp_type.set_active(self.cfg.touchpad_disable_while_typing)
        row_tp_type.connect("notify::active", lambda w, p: self._set_val("touchpad_disable_while_typing", w.get_active()))
        grp_touch.add(row_tp_type)

        page.add(grp_touch)

        return page

    def _set_val(self, prop: str, val):
        setattr(self.cfg, prop, val)
        self.win.mark_modified()
