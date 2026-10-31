"""
Advanced Configuration Page for Hyprland Config Manager.
Exposes dwindle/master layout details, compositor optimizations (VFR, VRR),
and miscellaneous Hyprland directives.
"""


class AdvancedPageBuilder:
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
        page.set_title("Advanced")
        page.set_icon_name("preferences-system-symbolic")

        # 1. Dwindle Layout Tuning
        grp_dwindle = Adw.PreferencesGroup()
        grp_dwindle.set_title("Dwindle Layout Options")
        grp_dwindle.set_description("Fine-tune binary-tree splitting and pseudotiling")

        row_pseudo = Adw.SwitchRow()
        row_pseudo.set_title("Pseudotiling (pseudotile)")
        row_pseudo.set_subtitle("Allow tiled windows to keep their floating size constraints")
        row_pseudo.set_active(True)
        grp_dwindle.add(row_pseudo)

        row_split = Adw.SwitchRow()
        row_split.set_title("Preserve Split Direction (preserve_split)")
        row_split.set_subtitle("Retain split directions when toggling windows")
        row_split.set_active(True)
        grp_dwindle.add(row_split)

        page.add(grp_dwindle)

        # 2. Compositor Rendering & Misc
        grp_misc = Adw.PreferencesGroup()
        grp_misc.set_title("Compositor & Rendering (misc)")

        row_vfr = Adw.SwitchRow()
        row_vfr.set_title("Variable Frame Rate (vfr)")
        row_vfr.set_subtitle("Reduce GPU/battery consumption when screen is static")
        row_vfr.set_active(True)
        grp_misc.add(row_vfr)

        row_logo = Adw.SwitchRow()
        row_logo.set_title("Disable Hyprland Default Splash & Anime Logo")
        row_logo.set_active(True)
        grp_misc.add(row_logo)

        row_warp = Adw.SwitchRow()
        row_warp.set_title("Disable Mouse Warping on Focus Change")
        row_warp.set_active(False)
        grp_misc.add(row_warp)

        page.add(grp_misc)

        return page
