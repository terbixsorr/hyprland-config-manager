"""
Config Engine for Hyprland Config Manager.
Coordinates parsing, data model extraction, in-place AST updating, and generation.
Preserves user comments, unrecognized settings, and multi-file source structures.
"""

import os
import re
from typing import List, Dict, Optional, Tuple, Any

from .ast_nodes import (
    ASTNode,
    ConfigFileAST,
    AssignmentNode,
    SectionNode,
    DirectiveNode,
    CommentNode,
    BlankLineNode,
    VariableNode,
    SourceNode,
    RawLineNode,
)
from .parser import HyprlandParser
from .generator import HyprlandGenerator
from .models import (
    MonitorConfig,
    WindowsConfig,
    AnimationsConfig,
    ANIMATION_PRESETS,
    AppearanceConfig,
    APPEARANCE_THEMES,
    KeybindItem,
    InputConfig,
    StartupItem,
    WorkspaceRule,
    WindowRuleItem,
    WallpaperConfig,
    EnvironmentConfig,
)


class HyprlandConfigEngine:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.discover_config_path()
        self.parser = HyprlandParser(base_dir=os.path.dirname(self.config_path))
        self.ast: Optional[ConfigFileAST] = None
        self.raw_original_content: str = ""

        # Models
        self.monitors: List[MonitorConfig] = []
        self.windows: WindowsConfig = WindowsConfig()
        self.animations: AnimationsConfig = AnimationsConfig()
        self.appearance: AppearanceConfig = AppearanceConfig()
        self.input_cfg: InputConfig = InputConfig()
        self.keybinds: List[KeybindItem] = []
        self.startup_items: List[StartupItem] = []
        self.workspace_rules: List[WorkspaceRule] = []
        self.window_rules: List[WindowRuleItem] = []
        self.env_cfg: EnvironmentConfig = EnvironmentConfig()
        self.wallpapers: WallpaperConfig = WallpaperConfig()
        self.variables: Dict[str, str] = {}
        self.sources: List[str] = []

    @staticmethod
    def discover_config_path() -> str:
        xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        primary = os.path.join(xdg_config, "hypr", "hyprland.conf")
        return primary

    def load_from_string(self, content: str, file_path: str = "hyprland.conf"):
        self.raw_original_content = content
        self.ast = self.parser.parse_string(content, file_path=file_path)
        self._extract_models_from_ast()

    def load_file(self, file_path: Optional[str] = None):
        path = file_path or self.config_path
        if not os.path.exists(path):
            # Create a clean default template if none exists
            content = self._get_default_template()
            self.load_from_string(content, file_path=path)
            return

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        self.load_from_string(content, file_path=path)

    def _get_default_template(self) -> str:
        return """# Hyprland Config - Generated / Managed by Hyprland Config Manager

# Monitors
monitor = ,preferred,auto,1

# Programs
$terminal = kitty
$fileManager = thunar
$menu = wofi --show drun

# Autostart
exec-once = waybar
exec-once = hyprpaper

# Environment
env = XCURSOR_SIZE,24
env = QT_QPA_PLATFORM,wayland

# Input
input {
    kb_layout = us,ru
    kb_options = grp:alt_shift_toggle
    follow_mouse = 1
    touchpad {
        natural_scroll = true
        tap-to-click = true
    }
    sensitivity = 0
}

# General
general {
    gaps_in = 5
    gaps_out = 15
    border_size = 2
    col.active_border = rgba(33ccffee) rgba(00ff99ee) 45deg
    col.inactive_border = rgba(595959aa)
    layout = dwindle
}

# Decoration
decoration {
    rounding = 8
    active_opacity = 1.0
    inactive_opacity = 0.85
    drop_shadow = true
    shadow_range = 10
    shadow_render_power = 3
    col.shadow = rgba(1a1a1aee)

    blur {
        enabled = true
        size = 5
        passes = 2
        new_optimizations = true
    }
}

# Animations
animations {
    enabled = true
    bezier = myBezier, 0.05, 0.9, 0.1, 1.05
    animation = windows, 1, 7, myBezier
    animation = windowsOut, 1, 7, default, popin 80%
    animation = border, 1, 10, default
    animation = fade, 1, 7, default
    animation = workspaces, 1, 6, default
}

# Layouts
dwindle {
    pseudotile = true
    preserve_split = true
}

# Keybindings
$mainMod = SUPER
bind = $mainMod, Q, exec, $terminal
bind = $mainMod, C, killactive,
bind = $mainMod, M, exit,
bind = $mainMod, E, exec, $fileManager
bind = $mainMod, V, togglefloating,
bind = $mainMod, R, exec, $menu
bind = $mainMod, P, pseudo,
bind = $mainMod, J, togglesplit,
bind = $mainMod, left, movefocus, l
bind = $mainMod, right, movefocus, r
bind = $mainMod, up, movefocus, u
bind = $mainMod, down, movefocus, d
bind = $mainMod, 1, workspace, 1
bind = $mainMod, 2, workspace, 2
bind = $mainMod, 3, workspace, 3
bind = $mainMod, 4, workspace, 4
bind = $mainMod, 5, workspace, 5
"""

    def _extract_models_from_ast(self):
        if not self.ast:
            return

        self.monitors = []
        self.keybinds = []
        self.startup_items = []
        self.workspace_rules = []
        self.window_rules = []
        self.variables = {}
        self.sources = []
        self.env_cfg.vars = {}

        # 1. Traverse top-level directives & variables
        for node in self.ast.nodes:
            if isinstance(node, VariableNode):
                self.variables[node.name] = node.value

            elif isinstance(node, SourceNode):
                self.sources.append(node.path)

            elif isinstance(node, DirectiveNode):
                d = node.directive
                val = node.value.strip()

                if d == "monitor":
                    self._parse_monitor_directive(val)

                elif d.startswith("bind"):
                    flag = d[4:] if len(d) > 4 else ""
                    self._parse_bind_directive(val, flag, node.comment)

                elif d in ("exec-once", "exec"):
                    self.startup_items.append(StartupItem(
                        command=val,
                        exec_type=d,
                        enabled=True,
                        comment=node.comment
                    ))

                elif d == "env":
                    parts = [p.strip() for p in val.split(",", 1)]
                    if len(parts) == 2:
                        self.env_cfg.vars[parts[0]] = parts[1]
                    elif len(parts) == 1:
                        self.env_cfg.vars[parts[0]] = ""

                elif d == "workspace":
                    self._parse_workspace_directive(val)

                elif d in ("windowrule", "windowrulev2"):
                    self._parse_windowrule_directive(d, val)

            elif isinstance(node, CommentNode):
                # Detect commented out exec-once or keybinds
                txt = node.text.strip()
                if txt.startswith("exec-once = ") or txt.startswith("exec = "):
                    parts = txt.split("=", 1)
                    t = parts[0].strip()
                    c = parts[1].strip()
                    self.startup_items.append(StartupItem(
                        command=c,
                        exec_type=t,
                        enabled=False,
                        comment="Disabled startup app"
                    ))

            elif isinstance(node, SectionNode):
                self._extract_from_section(node)

        # Do not inject fake monitors. If empty, query real monitors from hyprctl if available.
        if not self.monitors:
            try:
                from .hyprctl import HyprctlClient
                hyprctl = HyprctlClient()
                if hyprctl.is_available() and hyprctl.get_status().is_running:
                    real_mons = hyprctl.get_monitors()
                    for rm in real_mons:
                        m_name = rm.get("name", "")
                        if m_name:
                            w = rm.get("width", 1920)
                            h = rm.get("height", 1080)
                            rr = float(rm.get("refreshRate", 60.0))
                            x = rm.get("x", 0)
                            y = rm.get("y", 0)
                            scale = float(rm.get("scale", 1.0))
                            vrr = 1 if rm.get("vrr", False) else 0
                            self.monitors.append(MonitorConfig(
                                name=m_name,
                                resolution=f"{w}x{h}",
                                refresh_rate=rr,
                                position=f"{x}x{y}",
                                scale=scale,
                                vrr=vrr,
                                enabled=not rm.get("disabled", False)
                            ))
            except Exception:
                pass

    def _parse_monitor_directive(self, val: str):
        # Format: name,resolution@refresh,position,scale,extras...
        # or: ,preferred,auto,1
        # or: name,disable
        parts = [p.strip() for p in val.split(",")]
        if not parts:
            return
        name = parts[0]
        if len(parts) > 1 and parts[1].lower() == "disable":
            self.monitors.append(MonitorConfig(name=name, enabled=False))
            return

        res = "1920x1080"
        refresh = 60.0
        pos = "0x0"
        scale = 1.0
        vrr = 0
        transform = 0

        if len(parts) > 1:
            res_part = parts[1]
            if "@" in res_part:
                r_parts = res_part.split("@")
                res = r_parts[0]
                try:
                    refresh = float(r_parts[1])
                except ValueError:
                    refresh = 60.0
            else:
                res = res_part
                if res in ("preferred", "highrr", "highres"):
                    refresh = 0.0

        if len(parts) > 2:
            pos = parts[2]
        if len(parts) > 3:
            try:
                scale = float(parts[3])
            except ValueError:
                scale = 1.0

        for extra in parts[4:]:
            extra_clean = extra.lower().strip()
            if extra_clean.startswith("vrr"):
                v_split = extra_clean.split(",")
                try:
                    vrr = int(v_split[1]) if len(v_split) > 1 else 1
                except ValueError:
                    vrr = 1
            elif extra_clean.startswith("transform"):
                t_split = extra_clean.split(",")
                try:
                    transform = int(t_split[1]) if len(t_split) > 1 else 0
                except ValueError:
                    transform = 0

        self.monitors.append(MonitorConfig(
            name=name,
            resolution=res,
            refresh_rate=refresh,
            position=pos,
            scale=scale,
            vrr=vrr,
            transform=transform,
            enabled=True
        ))

    def _parse_bind_directive(self, val: str, flag: str, comment: str):
        # Format: mods, key, dispatcher, args
        parts = [p.strip() for p in val.split(",", 3)]
        mods = parts[0] if len(parts) > 0 else "SUPER"
        key = parts[1] if len(parts) > 1 else ""
        disp = parts[2] if len(parts) > 2 else ""
        args = parts[3] if len(parts) > 3 else ""

        self.keybinds.append(KeybindItem(
            modifier=mods,
            key=key,
            dispatcher=disp,
            arguments=args,
            flag=flag,
            comment=comment
        ))

    def _parse_workspace_directive(self, val: str):
        parts = [p.strip() for p in val.split(",")]
        if not parts:
            return
        ws_id = parts[0]
        mon = ""
        is_def = False
        is_pers = False
        gaps_in = None
        gaps_out = None

        for p in parts[1:]:
            if p.startswith("monitor:"):
                mon = p.split(":", 1)[1]
            elif p.startswith("default:"):
                is_def = p.split(":", 1)[1].lower() in ("true", "1")
            elif p.startswith("persistent:"):
                is_pers = p.split(":", 1)[1].lower() in ("true", "1")
            elif p.startswith("gapsin:"):
                try:
                    gaps_in = int(p.split(":", 1)[1])
                except ValueError:
                    pass
            elif p.startswith("gapsout:"):
                try:
                    gaps_out = int(p.split(":", 1)[1])
                except ValueError:
                    pass

        self.workspace_rules.append(WorkspaceRule(
            workspace_id=ws_id,
            monitor=mon,
            default=is_def,
            persistent=is_pers,
            gaps_in=gaps_in,
            gaps_out=gaps_out
        ))

    def _parse_windowrule_directive(self, directive: str, val: str):
        rule = WindowRuleItem(raw_rule=f"{directive} = {val}")
        if directive == "windowrulev2":
            # parse class / title / float
            parts = [p.strip() for p in val.split(",")]
            if parts:
                action = parts[0]
                if "float" in action:
                    rule.floating = True
                if "fullscreen" in action:
                    rule.fullscreen = True
                for f in parts[1:]:
                    if f.startswith("class:"):
                        c = f[6:].strip("^()$")
                        rule.app_class = c
                    elif f.startswith("title:"):
                        t = f[6:].strip("^()$")
                        rule.app_title = t
                    elif f.startswith("workspace"):
                        w = f.split(" ", 1)[1] if " " in f else ""
                        rule.workspace = w
        self.window_rules.append(rule)

    def _extract_from_section(self, sec: SectionNode):
        s_name = sec.name.lower()

        if s_name == "general":
            for n in sec.body:
                if isinstance(n, AssignmentNode):
                    k = n.key.strip()
                    v = n.value.strip()
                    if k == "border_size":
                        self.windows.border_size = int(v) if v.isdigit() else 2
                    elif k == "gaps_in":
                        self.windows.gaps_in = int(v) if v.isdigit() else 5
                    elif k == "gaps_out":
                        self.windows.gaps_out = int(v) if v.isdigit() else 15
                    elif k == "layout":
                        self.windows.layout = v
                    elif k == "col.active_border":
                        self.appearance.col_active_border = v
                    elif k == "col.inactive_border":
                        self.appearance.col_inactive_border = v

        elif s_name == "decoration":
            for n in sec.body:
                if isinstance(n, AssignmentNode):
                    k = n.key.strip()
                    v = n.value.strip()
                    if k == "rounding":
                        val_r = int(v) if v.isdigit() else 8
                        self.windows.rounding = val_r
                        self.appearance.rounding = val_r
                    elif k == "active_opacity":
                        try:
                            self.windows.active_opacity = float(v)
                        except ValueError:
                            pass
                    elif k == "inactive_opacity":
                        try:
                            self.windows.inactive_opacity = float(v)
                        except ValueError:
                            pass
                    elif k == "drop_shadow":
                        self.windows.drop_shadow = v.lower() in ("true", "1", "yes")
                    elif k == "shadow_range":
                        self.windows.shadow_range = int(v) if v.isdigit() else 10
                    elif k == "shadow_render_power":
                        self.windows.shadow_render_power = int(v) if v.isdigit() else 3
                    elif k == "col.shadow":
                        self.windows.shadow_color = v

                elif isinstance(n, SectionNode) and n.name.lower() == "blur":
                    for bn in n.body:
                        if isinstance(bn, AssignmentNode):
                            bk = bn.key.strip()
                            bv = bn.value.strip()
                            if bk == "enabled":
                                self.windows.blur_enabled = bv.lower() in ("true", "1", "yes")
                            elif bk == "size":
                                self.windows.blur_size = int(bv) if bv.isdigit() else 5
                            elif bk == "passes":
                                self.windows.blur_passes = int(bv) if bv.isdigit() else 2
                            elif bk == "new_optimizations":
                                self.windows.blur_new_optimizations = bv.lower() in ("true", "1", "yes")

        elif s_name == "input":
            for n in sec.body:
                if isinstance(n, AssignmentNode):
                    k = n.key.strip()
                    v = n.value.strip()
                    if k == "kb_layout":
                        self.input_cfg.kb_layout = v
                    elif k == "kb_variant":
                        self.input_cfg.kb_variant = v
                    elif k == "kb_options":
                        self.input_cfg.kb_options = v
                    elif k == "repeat_rate":
                        self.input_cfg.repeat_rate = int(v) if v.isdigit() else 50
                    elif k == "repeat_delay":
                        self.input_cfg.repeat_delay = int(v) if v.isdigit() else 300
                    elif k == "follow_mouse":
                        self.windows.follow_mouse = int(v) if v.isdigit() else 1
                    elif k == "sensitivity":
                        try:
                            self.input_cfg.mouse_sensitivity = float(v)
                        except ValueError:
                            pass
                    elif k == "accel_profile":
                        self.input_cfg.accel_profile = v
                    elif k == "natural_scroll":
                        self.input_cfg.natural_scroll = v.lower() in ("true", "1", "yes")

                elif isinstance(n, SectionNode) and n.name.lower() == "touchpad":
                    for tn in n.body:
                        if isinstance(tn, AssignmentNode):
                            tk = tn.key.strip()
                            tv = tn.value.strip()
                            if tk == "natural_scroll":
                                self.input_cfg.touchpad_natural_scroll = tv.lower() in ("true", "1", "yes")
                            elif tk == "tap-to-click":
                                self.input_cfg.touchpad_tap_to_click = tv.lower() in ("true", "1", "yes")
                            elif tk == "drag_lock":
                                self.input_cfg.touchpad_drag_lock = tv.lower() in ("true", "1", "yes")
                            elif tk == "disable_while_typing":
                                self.input_cfg.touchpad_disable_while_typing = tv.lower() in ("true", "1", "yes")

        elif s_name == "animations":
            for n in sec.body:
                if isinstance(n, AssignmentNode):
                    if n.key.strip() == "enabled":
                        self.animations.enabled = n.value.strip().lower() in ("true", "1", "yes")
                elif isinstance(n, DirectiveNode):
                    if n.directive == "bezier":
                        b_parts = [p.strip() for p in n.value.split(",", 1)]
                        if len(b_parts) == 2:
                            self.animations.bezier_curves[b_parts[0]] = b_parts[1]
                    elif n.directive == "animation":
                        # format: target, enabled, speed, curve, [style]
                        a_parts = [p.strip() for p in n.value.split(",")]
                        if len(a_parts) >= 4:
                            target = a_parts[0]
                            en = a_parts[1] in ("1", "true")
                            try:
                                spd = int(a_parts[2])
                            except ValueError:
                                spd = 6
                            crv = a_parts[3]
                            stl = a_parts[4] if len(a_parts) > 4 else ""
                            self.animations.animations[target] = {
                                "enabled": en,
                                "speed": spd,
                                "curve": crv,
                                "style": stl
                            }

    # =========================================================================
    # Synchronization: Update AST from Data Models
    # =========================================================================

    def _find_or_create_section(self, name: str) -> SectionNode:
        for node in self.ast.nodes:
            if isinstance(node, SectionNode) and node.name.lower() == name.lower():
                return node
        new_sec = SectionNode(name=name, body=[])
        self.ast.nodes.append(BlankLineNode())
        self.ast.nodes.append(new_sec)
        return new_sec

    def _set_assignment_in_section(self, section: SectionNode, key: str, value: str):
        for node in section.body:
            if isinstance(node, AssignmentNode) and node.key.strip() == key:
                node.value = value
                return
        section.body.append(AssignmentNode(key=key, value=value))

    def _set_nested_section_assignment(self, parent: SectionNode, sub_name: str, key: str, value: str):
        sub_sec = None
        for node in parent.body:
            if isinstance(node, SectionNode) and node.name.lower() == sub_name.lower():
                sub_sec = node
                break
        if not sub_sec:
            sub_sec = SectionNode(name=sub_name, body=[])
            parent.body.append(sub_sec)
        self._set_assignment_in_section(sub_sec, key, value)

    def sync_models_to_ast(self):
        """
        Applies model state back to AST nodes, keeping comments, custom directives, and structure.
        """
        if not self.ast:
            self.ast = ConfigFileAST(file_path=self.config_path)

        # 1. Update general section
        sec_gen = self._find_or_create_section("general")
        self._set_assignment_in_section(sec_gen, "gaps_in", str(self.windows.gaps_in))
        self._set_assignment_in_section(sec_gen, "gaps_out", str(self.windows.gaps_out))
        self._set_assignment_in_section(sec_gen, "border_size", str(self.windows.border_size))
        self._set_assignment_in_section(sec_gen, "col.active_border", self.appearance.col_active_border)
        self._set_assignment_in_section(sec_gen, "col.inactive_border", self.appearance.col_inactive_border)
        self._set_assignment_in_section(sec_gen, "layout", self.windows.layout)

        # 2. Update decoration section
        sec_dec = self._find_or_create_section("decoration")
        self._set_assignment_in_section(sec_dec, "rounding", str(self.windows.rounding))
        self._set_assignment_in_section(sec_dec, "active_opacity", f"{self.windows.active_opacity:.2f}")
        self._set_assignment_in_section(sec_dec, "inactive_opacity", f"{self.windows.inactive_opacity:.2f}")
        self._set_assignment_in_section(sec_dec, "drop_shadow", "true" if self.windows.drop_shadow else "false")
        self._set_assignment_in_section(sec_dec, "shadow_range", str(self.windows.shadow_range))
        self._set_assignment_in_section(sec_dec, "shadow_render_power", str(self.windows.shadow_render_power))
        self._set_assignment_in_section(sec_dec, "col.shadow", self.windows.shadow_color)

        self._set_nested_section_assignment(sec_dec, "blur", "enabled", "true" if self.windows.blur_enabled else "false")
        self._set_nested_section_assignment(sec_dec, "blur", "size", str(self.windows.blur_size))
        self._set_nested_section_assignment(sec_dec, "blur", "passes", str(self.windows.blur_passes))
        self._set_nested_section_assignment(sec_dec, "blur", "new_optimizations", "true" if self.windows.blur_new_optimizations else "false")

        # 3. Update input section
        sec_inp = self._find_or_create_section("input")
        self._set_assignment_in_section(sec_inp, "kb_layout", self.input_cfg.kb_layout)
        if self.input_cfg.kb_variant:
            self._set_assignment_in_section(sec_inp, "kb_variant", self.input_cfg.kb_variant)
        self._set_assignment_in_section(sec_inp, "kb_options", self.input_cfg.kb_options)
        self._set_assignment_in_section(sec_inp, "repeat_rate", str(self.input_cfg.repeat_rate))
        self._set_assignment_in_section(sec_inp, "repeat_delay", str(self.input_cfg.repeat_delay))
        self._set_assignment_in_section(sec_inp, "follow_mouse", str(self.windows.follow_mouse))
        self._set_assignment_in_section(sec_inp, "sensitivity", f"{self.input_cfg.mouse_sensitivity:.2f}")
        self._set_assignment_in_section(sec_inp, "accel_profile", self.input_cfg.accel_profile)
        self._set_assignment_in_section(sec_inp, "natural_scroll", "true" if self.input_cfg.natural_scroll else "false")

        self._set_nested_section_assignment(sec_inp, "touchpad", "natural_scroll", "true" if self.input_cfg.touchpad_natural_scroll else "false")
        self._set_nested_section_assignment(sec_inp, "touchpad", "tap-to-click", "true" if self.input_cfg.touchpad_tap_to_click else "false")
        self._set_nested_section_assignment(sec_inp, "touchpad", "drag_lock", "true" if self.input_cfg.touchpad_drag_lock else "false")
        self._set_nested_section_assignment(sec_inp, "touchpad", "disable_while_typing", "true" if self.input_cfg.touchpad_disable_while_typing else "false")

        # 4. Update animations section
        sec_anim = self._find_or_create_section("animations")
        # Keep non-bezier/non-animation assignments
        new_anim_body = []
        for n in sec_anim.body:
            if isinstance(n, AssignmentNode) and n.key == "enabled":
                continue
            if isinstance(n, DirectiveNode) and n.directive in ("bezier", "animation"):
                continue
            new_anim_body.append(n)

        new_anim_body.insert(0, AssignmentNode(key="enabled", value="true" if self.animations.enabled else "false"))

        for b_name, b_val in self.animations.bezier_curves.items():
            new_anim_body.append(DirectiveNode(directive="bezier", value=f"{b_name}, {b_val}"))

        for target, data in self.animations.animations.items():
            en_str = "1" if data.get("enabled", True) else "0"
            spd_str = str(data.get("speed", 6))
            crv_str = data.get("curve", "default")
            stl_str = data.get("style", "")
            val = f"{target}, {en_str}, {spd_str}, {crv_str}"
            if stl_str:
                val += f", {stl_str}"
            new_anim_body.append(DirectiveNode(directive="animation", value=val))

        sec_anim.body = new_anim_body

        # 5. Directives: monitors, binds, startup, env, workspace, windowrule
        # Filter existing ones out of root, then re-insert cleanly
        filtered_root = []
        manager_headers = {
            "=== Hyprland Config Manager Managed Directives ===",
            "Monitors",
            "Environment Variables",
            "Startup Applications",
            "Keybindings",
            "Workspace Rules",
            "Window Rules",
        }
        for n in self.ast.nodes:
            if isinstance(n, DirectiveNode):
                if n.directive in ("monitor", "workspace", "windowrule", "windowrulev2", "exec", "exec-once", "env"):
                    continue
                if n.directive.startswith("bind"):
                    continue
            elif isinstance(n, CommentNode):
                txt = n.text.strip()
                if txt.startswith("exec-once = ") or txt.startswith("exec = "):
                    continue
                if txt in manager_headers:
                    continue
            filtered_root.append(n)

        # Trim trailing blank lines from filtered root
        while filtered_root and isinstance(filtered_root[-1], BlankLineNode):
            filtered_root.pop()

        # Build list of new directive nodes
        directive_insertions: List[ASTNode] = [BlankLineNode(), CommentNode(text="=== Hyprland Config Manager Managed Directives ===")]

        # Monitors
        if self.monitors:
            directive_insertions.append(CommentNode(text="Monitors"))
            for m in self.monitors:
                directive_insertions.append(DirectiveNode(directive="monitor", value=m.to_directive_value()))

        # Environment
        if self.env_cfg.vars:
            directive_insertions.append(BlankLineNode())
            directive_insertions.append(CommentNode(text="Environment Variables"))
            for k, v in self.env_cfg.vars.items():
                directive_insertions.append(DirectiveNode(directive="env", value=f"{k},{v}"))

        # Startup
        if self.startup_items:
            directive_insertions.append(BlankLineNode())
            directive_insertions.append(CommentNode(text="Startup Applications"))
            for s in self.startup_items:
                if s.enabled:
                    directive_insertions.append(DirectiveNode(directive=s.exec_type, value=s.command, comment=s.comment))
                else:
                    directive_insertions.append(CommentNode(text=f"{s.exec_type} = {s.command}  # disabled"))

        # Keybindings
        if self.keybinds:
            directive_insertions.append(BlankLineNode())
            directive_insertions.append(CommentNode(text="Keybindings"))
            for kb in self.keybinds:
                pref = f"bind{kb.flag}" if kb.flag else "bind"
                v = f"{kb.modifier}, {kb.key}, {kb.dispatcher}"
                if kb.arguments:
                    v += f", {kb.arguments}"
                directive_insertions.append(DirectiveNode(directive=pref, value=v, comment=kb.comment))

        # Workspaces
        if self.workspace_rules:
            directive_insertions.append(BlankLineNode())
            directive_insertions.append(CommentNode(text="Workspace Rules"))
            for ws in self.workspace_rules:
                directive_insertions.append(DirectiveNode(directive="workspace", value=ws.to_directive().split("=", 1)[1].strip()))

        # Window Rules
        if self.window_rules:
            directive_insertions.append(BlankLineNode())
            directive_insertions.append(CommentNode(text="Window Rules"))
            for wr in self.window_rules:
                d_str = wr.to_directive()
                d_parts = d_str.split("=", 1)
                directive_insertions.append(DirectiveNode(directive=d_parts[0].strip(), value=d_parts[1].strip()))

        self.ast.nodes = filtered_root + directive_insertions

    def apply_profile_data(self, data: Dict[str, Any]):
        """
        Applies all settings from a profile data dictionary to the engine models.
        Supports windows, animations, appearance, input, and environment configurations.
        """
        if not isinstance(data, dict):
            return

        # 1. Appearance baseline (theme colors, baseline rounding)
        if "appearance" in data and isinstance(data["appearance"], dict):
            app_data = data["appearance"]
            if "theme_name" in app_data:
                t_name = app_data["theme_name"]
                self.appearance.theme_name = t_name
                if t_name in APPEARANCE_THEMES:
                    t_data = APPEARANCE_THEMES[t_name]
                    self.appearance.col_active_border = t_data["col_active_border"]
                    self.appearance.col_inactive_border = t_data["col_inactive_border"]
                    self.appearance.rounding = t_data["rounding"]
                    self.windows.rounding = t_data["rounding"]
                    self.windows.shadow_color = t_data["shadow_color"]
            if "col_active_border" in app_data:
                self.appearance.col_active_border = str(app_data["col_active_border"])
            if "col_inactive_border" in app_data:
                self.appearance.col_inactive_border = str(app_data["col_inactive_border"])
            if "rounding" in app_data:
                self.appearance.rounding = int(app_data["rounding"])
                self.windows.rounding = int(app_data["rounding"])

        # 2. Windows specific geometry and decoration (overrides theme defaults)
        if "windows" in data and isinstance(data["windows"], dict):
            for k, v in data["windows"].items():
                if hasattr(self.windows, k):
                    setattr(self.windows, k, v)

        # 3. Animations
        if "animations" in data and isinstance(data["animations"], dict):
            a_data = data["animations"]
            if "preset" in a_data:
                p_name = a_data["preset"]
                self.animations.preset = p_name
                if p_name in ANIMATION_PRESETS:
                    p_preset = ANIMATION_PRESETS[p_name]
                    self.animations.enabled = p_preset.get("enabled", self.animations.enabled)
                    for t_k, t_v in p_preset.get("animations", {}).items():
                        if t_k in self.animations.animations:
                            self.animations.animations[t_k].update(t_v)
                        else:
                            self.animations.animations[t_k] = dict(t_v)
            if "enabled" in a_data:
                self.animations.enabled = bool(a_data["enabled"])
            if "bezier_curves" in a_data and isinstance(a_data["bezier_curves"], dict):
                self.animations.bezier_curves.update(a_data["bezier_curves"])
            if "animations" in a_data and isinstance(a_data["animations"], dict):
                for k, v in a_data["animations"].items():
                    if isinstance(v, dict):
                        if k in self.animations.animations:
                            self.animations.animations[k].update(v)
                        else:
                            self.animations.animations[k] = v

        # 4. Input devices
        if "input" in data and isinstance(data["input"], dict):
            for k, v in data["input"].items():
                target_k = "mouse_sensitivity" if k == "sensitivity" else k
                if hasattr(self.input_cfg, target_k):
                    setattr(self.input_cfg, target_k, v)

        # 5. Environment variables
        if "env" in data and isinstance(data["env"], dict):
            for k, v in data["env"].items():
                self.env_cfg.vars[str(k)] = str(v)

    def generate_candidate_config(self) -> str:
        self.sync_models_to_ast()
        return HyprlandGenerator.generate(self.ast)

    def save(self, file_path: Optional[str] = None) -> str:
        path = file_path or self.config_path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        content = self.generate_candidate_config()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.raw_original_content = content
        return content
