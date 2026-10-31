"""
Monitors Configuration Page for Hyprland Config Manager.
Allows configuring resolution, refresh rate, scaling, position, VRR, rotation,
and active status for real detected and configured displays.
"""

from ...core.models import MonitorConfig


class MonitorsPageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine
        self.hyprctl = main_window.hyprctl

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        page = Adw.PreferencesPage()
        page.set_title("Monitors")
        page.set_icon_name("video-display-symbolic")

        # Discover real monitors from hyprctl if running
        real_monitors = self.hyprctl.get_monitors()
        configured_map = {m.name: m for m in self.engine.monitors}

        # Merge real detected monitors with config
        active_mon_names = set()
        for rm in real_monitors:
            name = rm.get("name", "")
            active_mon_names.add(name)
            if name not in configured_map:
                w = rm.get("width", 1920)
                h = rm.get("height", 1080)
                rr = float(rm.get("refreshRate", 60.0))
                x = rm.get("x", 0)
                y = rm.get("y", 0)
                scale = float(rm.get("scale", 1.0))
                vrr = 1 if rm.get("vrr", False) else 0
                new_mon = MonitorConfig(
                    name=name,
                    resolution=f"{w}x{h}",
                    refresh_rate=rr,
                    position=f"{x}x{y}",
                    scale=scale,
                    vrr=vrr,
                    enabled=not rm.get("disabled", False)
                )
                self.engine.monitors.append(new_mon)
                configured_map[name] = new_mon

        # Group for each monitor
        for mon in self.engine.monitors:
            grp = Adw.PreferencesGroup()
            is_detected = mon.name in active_mon_names
            status_text = " (Connected via Wayland)" if is_detected else " (Configured in hyprland.conf)"
            grp.set_title(f"Monitor: {mon.name}{status_text}")

            # Enabled Switch
            row_enable = Adw.SwitchRow()
            row_enable.set_title("Enable Monitor")
            row_enable.set_subtitle("Activate or disable output for this display")
            row_enable.set_active(mon.enabled)
            row_enable.connect("notify::active", self._make_bool_setter(mon, "enabled"))
            grp.add(row_enable)

            # Resolution Row
            row_res = Adw.EntryRow()
            row_res.set_title("Resolution (Width x Height)")
            row_res.set_text(mon.resolution)
            row_res.connect("changed", self._make_str_setter(mon, "resolution"))
            grp.add(row_res)

            # Refresh Rate Row
            row_rr = Adw.SpinRow.new_with_range(24.0, 360.0, 1.0)
            row_rr.set_title("Refresh Rate (Hz)")
            row_rr.set_value(mon.refresh_rate)
            row_rr.connect("notify::value", self._make_spin_setter(mon, "refresh_rate"))
            grp.add(row_rr)

            # Scaling Row
            row_scale = Adw.SpinRow.new_with_range(0.5, 4.0, 0.25)
            row_scale.set_title("Display Scale")
            row_scale.set_subtitle("Wayland fractional scale factor (1.0, 1.25, 1.5, 2.0...)")
            row_scale.set_value(mon.scale)
            row_scale.connect("notify::value", self._make_spin_setter(mon, "scale"))
            grp.add(row_scale)

            # Position Row
            row_pos = Adw.EntryRow()
            row_pos.set_title("Position (XxY)")
            row_pos.set_subtitle("Coordinates on virtual Wayland desktop (e.g. 0x0, 1920x0)")
            row_pos.set_text(mon.position)
            row_pos.connect("changed", self._make_str_setter(mon, "position"))
            grp.add(row_pos)

            # VRR (Adaptive Sync) Row
            row_vrr = Adw.ComboRow()
            row_vrr.set_title("Variable Refresh Rate (VRR / Adaptive Sync)")
            model_vrr = Gtk.StringList.new(["Off (0)", "Always On (1)", "Fullscreen Only (2)"])
            row_vrr.set_model(model_vrr)
            row_vrr.set_selected(mon.vrr if 0 <= mon.vrr <= 2 else 0)
            row_vrr.connect("notify::selected", self._make_combo_setter(mon, "vrr"))
            grp.add(row_vrr)

            # Rotation / Transform Row
            row_trans = Adw.ComboRow()
            row_trans.set_title("Orientation / Rotation")
            model_trans = Gtk.StringList.new(["Normal (0°)", "Rotated 90°", "Inverted 180°", "Rotated 270°"])
            row_trans.set_model(model_trans)
            row_trans.set_selected(mon.transform if 0 <= mon.transform <= 3 else 0)
            row_trans.connect("notify::selected", self._make_combo_setter(mon, "transform"))
            grp.add(row_trans)

            page.add(grp)

        # Group for Adding a Custom / Virtual Monitor
        add_grp = Adw.PreferencesGroup()
        btn_add = Gtk.Button(label="Add Display Configuration")
        btn_add.set_icon_name("list-add-symbolic")
        btn_add.connect("clicked", lambda b: self._add_new_monitor())
        add_grp.add(btn_add)
        page.add(add_grp)

        return page

    def _make_bool_setter(self, obj, prop):
        def setter(widget, param):
            setattr(obj, prop, widget.get_active())
            self.win.mark_modified()
        return setter

    def _make_str_setter(self, obj, prop):
        def setter(widget):
            setattr(obj, prop, widget.get_text().strip())
            self.win.mark_modified()
        return setter

    def _make_spin_setter(self, obj, prop):
        def setter(widget, param):
            setattr(obj, prop, widget.get_value())
            self.win.mark_modified()
        return setter

    def _make_combo_setter(self, obj, prop):
        def setter(widget, param):
            setattr(obj, prop, widget.get_selected())
            self.win.mark_modified()
        return setter

    def _add_new_monitor(self):
        new_name = f"DP-{len(self.engine.monitors) + 1}"
        new_mon = MonitorConfig(name=new_name, resolution="1920x1080", refresh_rate=60.0, position="auto", scale=1.0)
        self.engine.monitors.append(new_mon)
        self.win.mark_modified()
        self.win.refresh_current_page()
