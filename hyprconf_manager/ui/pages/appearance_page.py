"""
Appearance & Theming Page for Hyprland Config Manager.
Allows selecting pre-configured color schemes (Catppuccin, Tokyo Night, Gruvbox,
Nord, Dracula, AMOLED, Dark, Light) and customizing border gradients and accents.
"""

from ...core.models import APPEARANCE_THEMES


class AppearancePageBuilder:
    def __init__(self, main_window):
        self.win = main_window
        self.engine = main_window.engine
        self.cfg = main_window.engine.appearance

    def build(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from gi.repository import Gtk, Adw
        except ImportError:
            return None

        page = Adw.PreferencesPage()
        page.set_title("Appearance")
        page.set_icon_name("preferences-desktop-theme-symbolic")

        # 1. Preset Themes
        grp_themes = Adw.PreferencesGroup()
        grp_themes.set_title("Color Schemes & Themes")
        grp_themes.set_description("Select a curated color scheme or craft your own")

        row_theme = Adw.ComboRow()
        row_theme.set_title("Active Theme Preset")
        theme_names = list(APPEARANCE_THEMES.keys()) + ["Custom"]
        model_themes = Gtk.StringList.new(theme_names)
        row_theme.set_model(model_themes)

        cur_idx = theme_names.index(self.cfg.theme_name) if self.cfg.theme_name in theme_names else len(theme_names) - 1
        row_theme.set_selected(cur_idx)

        grp_themes.add(row_theme)
        page.add(grp_themes)

        # 2. Border & Accents
        grp_borders = Adw.PreferencesGroup()
        grp_borders.set_title("Window Borders & Edge Lighting")

        # Active Border
        row_act_border = Adw.EntryRow()
        row_act_border.set_title("Active Border Color (RGBA / Gradient)")
        row_act_border.set_text(self.cfg.col_active_border)
        grp_borders.add(row_act_border)

        # Inactive Border
        row_inact_border = Adw.EntryRow()
        row_inact_border.set_title("Inactive Border Color")
        row_inact_border.set_text(self.cfg.col_inactive_border)
        grp_borders.add(row_inact_border)

        # Corner Rounding
        row_rounding = Adw.SpinRow.new_with_range(0, 30, 1)
        row_rounding.set_title("Border Corner Rounding")
        row_rounding.set_value(self.cfg.rounding)
        grp_borders.add(row_rounding)

        # Theme selection listener
        def on_theme_selected(widget, param):
            selected_name = theme_names[widget.get_selected()]
            self.cfg.theme_name = selected_name
            if selected_name in APPEARANCE_THEMES:
                theme_data = APPEARANCE_THEMES[selected_name]
                self.cfg.col_active_border = theme_data["col_active_border"]
                self.cfg.col_inactive_border = theme_data["col_inactive_border"]
                self.cfg.rounding = theme_data["rounding"]

                # Update Windows config model as well
                self.engine.windows.rounding = theme_data["rounding"]
                self.engine.windows.shadow_color = theme_data["shadow_color"]

                row_act_border.set_text(self.cfg.col_active_border)
                row_inact_border.set_text(self.cfg.col_inactive_border)
                row_rounding.set_value(self.cfg.rounding)

            self.win.mark_modified()

        row_theme.connect("notify::selected", on_theme_selected)

        row_act_border.connect("changed", lambda w: self._on_border_changed("col_active_border", w.get_text()))
        row_inact_border.connect("changed", lambda w: self._on_border_changed("col_inactive_border", w.get_text()))
        row_rounding.connect("notify::value", lambda w, p: self._on_rounding_changed(int(w.get_value())))

        page.add(grp_borders)

        return page

    def _on_border_changed(self, prop: str, val: str):
        setattr(self.cfg, prop, val.strip())
        self.cfg.theme_name = "Custom"
        self.win.mark_modified()

    def _on_rounding_changed(self, val: int):
        self.cfg.rounding = val
        self.engine.windows.rounding = val
        self.win.mark_modified()
