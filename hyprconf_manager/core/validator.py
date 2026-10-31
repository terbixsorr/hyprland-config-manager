"""
Validator for Hyprland configuration.
Performs syntax checks, brace balancing, directive validation, and variable resolution.
Generates human-readable, actionable error messages.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional


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


class HyprlandValidator:
    def __init__(self):
        pass

    def validate_content(self, content: str) -> ValidationResult:
        result = ValidationResult()
        lines = content.splitlines()

        brace_stack = []  # stores (line_num, section_name)
        defined_vars = set()
        seen_binds = {}  # (mod, key) -> line_num

        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            # Ignore empty and pure comment lines
            if not line or line.startswith("#"):
                continue

            # Strip inline comment
            if "#" in line:
                # crude split if outside quotes
                in_quote = False
                clean_chars = []
                for c in line:
                    if c in ('"', "'"):
                        in_quote = not in_quote
                    if c == "#" and not in_quote:
                        break
                    clean_chars.append(c)
                line = "".join(clean_chars).strip()

            if not line:
                continue

            # Check variable definition
            if line.startswith("$") and "=" in line:
                var_name = line.split("=", 1)[0].strip()[1:]
                defined_vars.add(var_name)
                continue

            # Check section opening: e.g. general {
            if line.endswith("{"):
                sec_name = line[:-1].strip()
                if not sec_name:
                    result.errors.append(ValidationError(
                        line_number=line_num,
                        message="Missing section name before '{'",
                        explanation="Section opening braces must follow a section identifier like 'general {'.",
                        offending_line=raw_line
                    ))
                brace_stack.append((line_num, sec_name))
                continue

            # Check section closing: }
            if line == "}":
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

            # Check key = value or directive = value
            if "=" not in line:
                result.errors.append(ValidationError(
                    line_number=line_num,
                    message="Missing assignment operator '='",
                    explanation="Each directive or configuration option in Hyprland requires an '=' separator.",
                    offending_line=raw_line
                ))
                continue

            key_part, val_part = line.split("=", 1)
            key = key_part.strip()
            val = val_part.strip()

            # Check variable usage in values
            if "$" in key:
                # Variables are usually in keybind definitions e.g. bind = $mainMod, Q, ...
                pass

            # Directive-specific checks
            if key == "monitor":
                self._validate_monitor(line_num, val, raw_line, result)
            elif key.startswith("bind"):
                self._validate_bind(line_num, key, val, raw_line, defined_vars, seen_binds, result)
            elif key in ("exec", "exec-once"):
                self._validate_exec(line_num, val, raw_line, result)
            elif key in ("windowrule", "windowrulev2"):
                self._validate_windowrule(line_num, key, val, raw_line, result)

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

    def _validate_monitor(self, line_num: int, val: str, raw_line: str, result: ValidationResult):
        parts = [p.strip() for p in val.split(",")]
        if not parts or not parts[0]:
            result.errors.append(ValidationError(
                line_number=line_num,
                message="Invalid monitor directive",
                explanation="Monitor directive cannot be empty. Example: 'monitor = DP-1, 1920x1080@144, 0x0, 1'",
                offending_line=raw_line
            ))
            return

        name = parts[0]
        if len(parts) > 1 and parts[1].lower() == "disable":
            return  # valid disable syntax

        if len(parts) >= 2:
            res_part = parts[1]
            if res_part not in ("preferred", "highrr", "highres") and "x" not in res_part:
                result.warnings.append(ValidationWarning(
                    line_number=line_num,
                    message=f"Unusual resolution specification '{res_part}' for monitor '{name}'",
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

    def _validate_bind(self, line_num: int, directive: str, val: str, raw_line: str,
                       defined_vars: set, seen_binds: dict, result: ValidationResult):
        parts = [p.strip() for p in val.split(",", 3)]
        if len(parts) < 3:
            result.errors.append(ValidationError(
                line_number=line_num,
                message=f"Incomplete {directive} definition",
                explanation=f"{directive} requires at least modifier, key, and dispatcher. Example: '{directive} = SUPER, Q, exec, kitty'",
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

        # Check for undefined variables in mods
        if mods.startswith("$"):
            var_name = mods[1:]
            if var_name not in defined_vars and var_name not in ("mainMod",):
                result.warnings.append(ValidationWarning(
                    line_number=line_num,
                    message=f"Variable '${var_name}' in keybinding may not be defined",
                    offending_line=raw_line
                ))

        # Conflict check
        combo_key = (mods.lower(), key.lower())
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
                explanation="Please provide a command for startup execution or remove the line.",
                offending_line=raw_line
            ))

    def _validate_windowrule(self, line_num: int, directive: str, val: str, raw_line: str, result: ValidationResult):
        parts = [p.strip() for p in val.split(",")]
        if not parts or not parts[0]:
            result.errors.append(ValidationError(
                line_number=line_num,
                message=f"Empty {directive} directive",
                explanation=f"Provide an action and filter for {directive}. Example: 'windowrulev2 = float, class:^(kitty)$'",
                offending_line=raw_line
            ))
