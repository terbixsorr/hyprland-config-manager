"""
Parser for Hyprland configuration files.
Builds an AST representation while preserving whitespace, comments, order, and unknown directives.
"""

import os
import re
from typing import List, Tuple, Optional
from .ast_nodes import (
    ASTNode,
    BlankLineNode,
    CommentNode,
    VariableNode,
    AssignmentNode,
    DirectiveNode,
    SourceNode,
    SectionNode,
    RawLineNode,
    ConfigFileAST,
)

RE_VAR = re.compile(r"^\$([a-zA-Z0-9_-]+)\s*=\s*(.*)$")
RE_SECTION_START = re.compile(r"^([a-zA-Z0-9_:-]+)\s*\{$")
RE_ASSIGN = re.compile(r"^([a-zA-Z0-9_.:-]+)\s*=\s*(.*)$")

REPETITIVE_DIRECTIVES = {
    "monitor",
    "bind",
    "bindm",
    "bindl",
    "binde",
    "bindr",
    "windowrule",
    "windowrulev2",
    "layerrule",
    "exec",
    "exec-once",
    "env",
    "workspace",
    "bezier",
    "animation",
    "submap",
    "plugin",
}


def _split_inline_comment(line: str) -> Tuple[str, str]:
    """
    Splits a line into code and comment, taking care not to split inside quotes.
    e.g. 'border_size = 2 # default size' -> ('border_size = 2', 'default size')
    """
    in_quote = False
    quote_char = ""
    for i, char in enumerate(line):
        if char in ('"', "'"):
            if not in_quote:
                in_quote = True
                quote_char = char
            elif quote_char == char:
                in_quote = False
        elif char == "#" and not in_quote:
            return line[:i].strip(), line[i + 1:].strip()
    return line.strip(), ""


class HyprlandParser:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.expanduser("~/.config/hypr")

    def parse_string(self, content: str, file_path: str = "hyprland.conf") -> ConfigFileAST:
        lines = content.splitlines()
        root_nodes: List[ASTNode] = []
        section_stack: List[Tuple[SectionNode, List[ASTNode]]] = []

        for line_num, raw_line in enumerate(lines, start=1):
            stripped = raw_line.strip()

            # 1. Blank line
            if not stripped:
                blank = BlankLineNode(source_file=file_path, line_number=line_num)
                if section_stack:
                    section_stack[-1][0].body.append(blank)
                else:
                    root_nodes.append(blank)
                continue

            # 2. Pure comment line
            if stripped.startswith("#"):
                comment = CommentNode(
                    source_file=file_path,
                    line_number=line_num,
                    text=stripped[1:].strip()
                )
                if section_stack:
                    section_stack[-1][0].body.append(comment)
                else:
                    root_nodes.append(comment)
                continue

            # 3. Section closing
            if stripped == "}":
                if section_stack:
                    closed_sec, _ = section_stack.pop()
                    # Closed section was already appended to its parent's body when opened
                else:
                    # Unbalanced closing brace preserved as raw
                    raw = RawLineNode(source_file=file_path, line_number=line_num, raw=raw_line)
                    root_nodes.append(raw)
                continue

            code_part, comment_part = _split_inline_comment(stripped)

            # 4. Check for section closing at end of a line or inline section
            # Check Section Start: e.g. "general {"
            sec_match = RE_SECTION_START.match(code_part)
            if sec_match:
                sec_name = sec_match.group(1)
                new_sec = SectionNode(
                    source_file=file_path,
                    line_number=line_num,
                    name=sec_name,
                    body=[],
                    comment=comment_part
                )
                if section_stack:
                    section_stack[-1][0].body.append(new_sec)
                else:
                    root_nodes.append(new_sec)
                section_stack.append((new_sec, new_sec.body))
                continue

            # 5. Check variable definition: $mainMod = SUPER
            var_match = RE_VAR.match(code_part)
            if var_match:
                v_name = var_match.group(1)
                v_val = var_match.group(2).strip()
                var_node = VariableNode(
                    source_file=file_path,
                    line_number=line_num,
                    name=v_name,
                    value=v_val,
                    comment=comment_part
                )
                if section_stack:
                    section_stack[-1][0].body.append(var_node)
                else:
                    root_nodes.append(var_node)
                continue

            # 6. Check assignment / directive
            assign_match = RE_ASSIGN.match(code_part)
            if assign_match:
                key = assign_match.group(1).strip()
                val = assign_match.group(2).strip()

                if key == "source":
                    src_node = SourceNode(
                        source_file=file_path,
                        line_number=line_num,
                        path=val,
                        comment=comment_part
                    )
                    if section_stack:
                        section_stack[-1][0].body.append(src_node)
                    else:
                        root_nodes.append(src_node)
                    continue

                if key in REPETITIVE_DIRECTIVES:
                    dir_node = DirectiveNode(
                        source_file=file_path,
                        line_number=line_num,
                        directive=key,
                        value=val,
                        comment=comment_part
                    )
                    if section_stack:
                        section_stack[-1][0].body.append(dir_node)
                    else:
                        root_nodes.append(dir_node)
                    continue

                # Standard assignment (key = value)
                ass_node = AssignmentNode(
                    source_file=file_path,
                    line_number=line_num,
                    key=key,
                    value=val,
                    comment=comment_part
                )
                if section_stack:
                    section_stack[-1][0].body.append(ass_node)
                else:
                    root_nodes.append(ass_node)
                continue

            # Fallback: line not matching any specific grammar
            raw_node = RawLineNode(
                source_file=file_path,
                line_number=line_num,
                raw=raw_line
            )
            if section_stack:
                section_stack[-1][0].body.append(raw_node)
            else:
                root_nodes.append(raw_node)

        return ConfigFileAST(file_path=file_path, nodes=root_nodes)

    def parse_file(self, file_path: str) -> ConfigFileAST:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return self.parse_string(content, file_path=file_path)
