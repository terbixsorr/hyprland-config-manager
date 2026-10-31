"""
Validator for Hyprland configuration.
Performs strict syntax checking: brace balancing, unclosed quotes,
variable resolution, directive formatting, range validations, and conflict audits.
Generates human-readable, actionable error messages with exact line references.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Tuple


@dataclass
class ValidationError:
    line_number: int
    message: str
    explanation: str
    offending_line: str = ""


@dataclass
class ValidationWarning:
    line_number: int
    message: str
    offending_line: str = ""


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)

    def summary(self) -> str:
        if self.is_valid and not self.warnings:
            return "Configuration is valid and ready to apply."
        if not self.is_valid:
            lines = [f"Found {len(self.errors)} error(s):"]
            for err in self.errors:
                lines.append(f"  • Line {err.line_number}: {err.message} — {err.explanation}")
            return "\n".join(lines)
        return f"Configuration is valid with {len(self.warnings)} warning(s)."


KNOWN_SECTIONS = {
    "general", "decoration", "animations", "input", "touchpad",
    "dwindle", "master", "gestures", "misc", "binds", "xwayland",
    "opengl", "render", "cursor", "ecosystem", "plugin", "blur"
}

NUMERIC_NON_NEG_KEYS = {
    "gaps_in", "gaps_out", "border_size", "rounding", "shadow_range",
    "shadow_render_power", "blur_size", "blur_passes"
}


class HyprlandValidator:
    def __init__(self):
        pass

    def validate_content(self, content: str) -> ValidationResult:
        result = ValidationResult()
        lines = content.splitlines()

        brace_stack: List[Tuple[int, str]] = []  # (line_num, section_name)
        defined_vars: Set[str] = set()
        seen_binds: Dict[Tuple[str, str, str], int] = {}  # (flag, mod, key) -> line_num

        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            # Ignore empty lines and pure comment lines
            if not line or line.startswith("#"):
                continue

            # 1. Quote balancing & comment stripping
            cleaned_line, quote_err = self._strip_comment_and_check_quotes(line)
            if quote_err:
                result.errors.append(ValidationError(
                    line_number=line_num,
                    message="Unclosed quote detected",
                    explanation=quote_err,
                    offending_line=raw_line
                ))
                continue

            if not cleaned_line:
                continue

            # 2. Check variable definitions: $var = value
            if cleaned_line.startswith("$") and "=" in cleaned_line:
                var_name = cleaned_line.split("=", 1)[0].strip()[1:]
                if not re.match(r"^[a-zA-Z0-9_-]+$", var_name):
                    result.errors.append(ValidationError(
                        line_number=line_num,
                        message=f"Invalid variable name '${var_name}'",
                        explanation="Variable names must contain only alphanumeric characters, underscores, or dashes.",
                        offending_line=raw_line
                    ))
                else:
                    defined_vars.add(var_name)
                continue

            # 3. Check section opening: section_name {
            if cleaned_line.endswith("{"):
                sec_name = cleaned_line[:-1].strip()
                if not sec_name:
                    result.errors.append(ValidationError(
                        line_number=line_num,
                        message="Missing section name before '{'",
                        explanation="Section opening braces must follow an identifier like 'general {'.",
                        offending_line=raw_line
                    ))
                elif not re.match(r"^[a-zA-Z0-9_:-]+$", sec_name):
                    result.errors.append(ValidationError(
                        line_number=line_num,
                        message=f"Invalid section name '{sec_name}'",
                        explanation="Section names must contain only letters, numbers, underscores, and colons.",
                        offending_line=raw_line
                    ))
                elif sec_name.lower() not in KNOWN_SECTIONS and ":" not in sec_name:
                    result.warnings.append(ValidationWarning(
                        line_number=line_num,
                        message=f"Unrecognized or plugin section '{sec_name}'",
                        offending_line=raw_line
                    ))
                brace_stack.append((line_num, sec_name))
                continue

            # 4. Check section closing: }
            if cleaned_line == "}":
                if not brace_stack:
                    result.errors.append(ValidationError(
                        line_number=line_num,
                        message="Unmatched closing brace '}'",
                        explanation="A closing brace '}' was found without a corresponding open section '{'.",
                        offending_line=raw_line
                    ))
                else:
                    brace_stack.pop()
                continue

            # 5. Check assignments and directives: key = value
            if "=" not in cleaned_line:
                result.errors.append(ValidationError(
                    line_number=line_num,
                    message="Missing assignment operator '='",
                    explanation="Each directive or setting requires an '=' separator (e.g. 'border_size = 2').",
                    offending_line=raw_line
                ))
                continue

            key_part, val_part = cleaned_line.split("=", 1)
            key = key_part.strip()
            val = val_part.strip()

            if not key:
                result.errors.append(ValidationError(
                    line_number=line_num,
                    message="Missing configuration key before '='",
                    explanation="A directive or option key cannot be empty.",
                    offending_line=raw_line
                ))
                continue

            # Directive-specific validations
            if key == "monitor":
                self._validate_monitor(line_num, val, raw_line, result)
            elif key.startswith("bind"):
                flag = key[4:] if len(key) > 4 else ""
                self._validate_bind(line_num, key, flag, val, raw_line, defined_vars, seen_binds, result)
            elif key in ("exec", "exec-once"):
                self._validate_exec(line_num, val, raw_line, result)
            elif key in ("windowrule", "windowrulev2"):
                self._validate_windowrule(line_num, key, val, raw_line, result)
            elif key == "workspace":
                self._validate_workspace(line_num, val, raw_line, result)
            elif key in NUMERIC_NON_NEG_KEYS:
                self._validate_non_negative_int(line_num, key, val, raw_line, result)
            elif key in ("active_opacity", "inactive_opacity", "fullscreen_opacity"):
                self._validate_opacity(line_num, key, val, raw_line, result)
            elif key == "follow_mouse":
                if val not in ("0", "1", "2", "3"):
                    result.warnings.append(ValidationWarning(
                        line_number=line_num,
                        message=f"Value for 'follow_mouse' is usually 0, 1, 2, or 3, got '{val}'",
                        offending_line=raw_line
                    ))

        # Check for unclosed braces
        while brace_stack:
            open_line, sec_name = brace_stack.pop()
            result.errors.append(ValidationError(
                line_number=open_line,
                message=f"Unclosed section '{sec_name}'",
                explanation=f"The section '{sec_name}' opened on line {open_line} is missing a closing brace '}}'.",
                offending_line=f"{sec_name} {{"
            ))

        if result.errors:
            result.is_valid = False

        return result

    def _strip_comment_and_check_quotes(self, line: str) -> Tuple[str, Optional[str]]:
        in_quote = False
        quote_char = ""
        clean_chars = []
        for i, c in enumerate(line):
            if c in ('"', "'"):
                if not in_quote:
                    in_quote = True
                    quote_char = c
                elif quote_char == c:
                    in_quote = False
                clean_chars.append(c)
            elif c == "#" and not in_quote:
                break
            else:
                clean_chars.append(c)

        if in_quote:
            return "", f"Mismatched or unclosed quote ({quote_char}) in line."
        return "".join(clean_chars).strip(), None

    def _validate_monitor(self, line_num: int, val: str, raw_line: str, result: ValidationResult):
        parts = [p.strip() for p in val.split(",")]
        if not parts or not any(parts):
            result.errors.append(ValidationError(
                line_number=line_num,
                message="Invalid monitor directive",
                explanation="Monitor directive cannot be empty. Example: 'monitor = DP-1, 1920x1080@144, 0x0, 1' or 'monitor = ,preferred,auto,1'.",
                offending_line=raw_line
            ))
            return

        name = parts[0]
        # Wildcard monitor is valid in Hyprland: monitor = ,preferred,auto,1
        if not name and len(parts) == 1:
            result.errors.append(ValidationError(
                line_number=line_num,
                message="Incomplete monitor directive",
                explanation="Specify at least resolution/mode. Example: 'monitor = ,preferred,auto,1'.",
                offending_line=raw_line
            ))
            return

        if len(parts) > 1 and parts[1].lower() == "disable":
            return  # valid disable syntax

        if len(parts) >= 2:
            res_part = parts[1]
            if res_part and res_part not in ("preferred", "highrr", "highres") and "x" not in res_part:
                result.warnings.append(ValidationWarning(
                    line_number=line_num,
                    message=f"Unusual resolution specification '{res_part}' for monitor '{name or 'Default'}'",
                    offending_line=raw_line
                ))

        if len(parts) >= 4:
            scale_part = parts[3]
            try:
                sc = float(scale_part)
                if sc <= 0:
                    result.errors.append(ValidationError(
                        line_number=line_num,
                        message=f"Invalid scale factor '{scale_part}'",
                        explanation="Monitor scale factor must be a positive number (e.g. 1, 1.25, 1.5, 2).",
                        offending_line=raw_line
                    ))
            except ValueError:
                result.errors.append(ValidationError(
                    line_number=line_num,
                    message=f"Non-numeric scale factor '{scale_part}'",
                    explanation="Scale factor must be numeric (e.g. 1.0 or 1.5).",
                    offending_line=raw_line
                ))

    def _validate_bind(self, line_num: int, directive: str, flag: str, val: str, raw_line: str,
                       defined_vars: Set[str], seen_binds: Dict[Tuple[str, str, str], int], result: ValidationResult):
        parts = [p.strip() for p in val.split(",", 3)]
        if len(parts) < 3:
            result.errors.append(ValidationError(
                line_number=line_num,
                message=f"Incomplete {directive} definition",
                explanation=f"{directive} requires modifier, key, and dispatcher. Example: '{directive} = SUPER, Q, exec, kitty'",
                offending_line=raw_line
            ))
            return

        mods, key, dispatcher = parts[0], parts[1], parts[2]
        if not key:
            result.errors.append(ValidationError(
                line_number=line_num,
                message="Keybinding key is empty",
                explanation="Specify a valid key name or symbol (e.g. 'Q', 'Return', 'Space').",
                offending_line=raw_line
            ))
            return

        if not dispatcher:
            result.errors.append(ValidationError(
                line_number=line_num,
                message="Keybinding dispatcher action is empty",
                explanation="Specify a valid dispatcher like 'exec', 'killactive', 'workspace', or 'togglefloating'.",
                offending_line=raw_line
            ))
            return

        # Check for undefined variables in mods
        if mods.startswith("$"):
            var_name = mods[1:]
            if var_name not in defined_vars and var_name not in ("mainMod",):
                result.warnings.append(ValidationWarning(
                    line_number=line_num,
                    message=f"Variable '${var_name}' in keybinding may not be defined",
                    offending_line=raw_line
                ))

        # Conflict check respecting flag (mouse binds bindm don't conflict with key binds bind)
        combo_key = (flag.lower(), mods.lower(), key.lower())
        if combo_key in seen_binds:
            prev_line = seen_binds[combo_key]
            result.warnings.append(ValidationWarning(
                line_number=line_num,
                message=f"Keybinding '{mods} + {key}' conflicts with earlier binding on line {prev_line}",
                offending_line=raw_line
            ))
        else:
            seen_binds[combo_key] = line_num

    def _validate_exec(self, line_num: int, val: str, raw_line: str, result: ValidationResult):
        if not val.strip():
            result.errors.append(ValidationError(
                line_number=line_num,
                message="Empty exec/exec-once command",
                explanation="Please provide a command for startup execution or remove the directive.",
                offending_line=raw_line
            ))

    def _validate_windowrule(self, line_num: int, directive: str, val: str, raw_line: str, result: ValidationResult):
        parts = [p.strip() for p in val.split(",")]
        if not parts or not parts[0]:
            result.errors.append(ValidationError(
                line_number=line_num,
                message=f"Empty {directive} directive",
                explanation=f"Provide an action and filter for {directive}. Example: '{directive} = float, class:^(kitty)$'",
                offending_line=raw_line
            ))

    def _validate_workspace(self, line_num: int, val: str, raw_line: str, result: ValidationResult):
        parts = [p.strip() for p in val.split(",")]
        if not parts or not parts[0]:
            result.errors.append(ValidationError(
                line_number=line_num,
                message="Empty workspace directive",
                explanation="Provide at least a workspace identifier (e.g. 'workspace = 1, monitor:DP-1').",
                offending_line=raw_line
            ))

    def _validate_non_negative_int(self, line_num: int, key: str, val: str, raw_line: str, result: ValidationResult):
        try:
            v = int(val)
            if v < 0:
                result.errors.append(ValidationError(
                    line_number=line_num,
                    message=f"Negative value for '{key}': {val}",
                    explanation=f"Option '{key}' must be a non-negative integer.",
                    offending_line=raw_line
                ))
        except ValueError:
            result.warnings.append(ValidationWarning(
                line_number=line_num,
                message=f"Expected integer for '{key}', got '{val}'",
                offending_line=raw_line
            ))

    def _validate_opacity(self, line_num: int, key: str, val: str, raw_line: str, result: ValidationResult):
        try:
            v = float(val)
            if not (0.0 <= v <= 1.0):
                result.errors.append(ValidationError(
                    line_number=line_num,
                    message=f"Opacity out of bounds for '{key}': {val}",
                    explanation="Opacity values in Hyprland must be between 0.0 and 1.0.",
                    offending_line=raw_line
                ))
        except ValueError:
            result.warnings.append(ValidationWarning(
                line_number=line_num,
                message=f"Expected numeric float for '{key}', got '{val}'",
                offending_line=raw_line
            ))
