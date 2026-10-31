"""
Generator for Hyprland configuration files.
Renders AST back to text and formats sections cleanly.
"""

import difflib
from typing import List, Tuple
from .ast_nodes import ConfigFileAST


class HyprlandGenerator:
    @staticmethod
    def generate(ast: ConfigFileAST) -> str:
        return ast.to_string()

    @staticmethod
    def compute_diff(old_text: str, new_text: str, old_label: str = "current", new_label: str = "proposed") -> str:
        """
        Computes a unified diff between old and new configuration text.
        """
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_label,
            tofile=new_label,
            n=3
        )
        return "".join(diff)

    @staticmethod
    def get_diff_stats(diff_text: str) -> Tuple[int, int]:
        """
        Returns count of (added_lines, removed_lines)
        """
        added = 0
        removed = 0
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1
        return added, removed
