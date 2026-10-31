"""
AST (Abstract Syntax Tree) nodes for Hyprland configuration files.
Preserves full document structure, comments, whitespace, and custom directives.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ASTNode:
    source_file: str = ""
    line_number: int = 0


@dataclass
class BlankLineNode(ASTNode):
    def to_string(self, indent: int = 0) -> str:
        return ""


@dataclass
class CommentNode(ASTNode):
    text: str = ""

    def to_string(self, indent: int = 0) -> str:
        pad = "    " * indent
        if not self.text:
            return f"{pad}#"
        # If text already starts with space, don't duplicate
        space = "" if self.text.startswith(" ") else " "
        return f"{pad}#{space}{self.text}"


@dataclass
class VariableNode(ASTNode):
    name: str = ""
    value: str = ""
    comment: str = ""

    def to_string(self, indent: int = 0) -> str:
        pad = "    " * indent
        comm = f" # {self.comment}" if self.comment else ""
        return f"{pad}${self.name} = {self.value}{comm}"


@dataclass
class AssignmentNode(ASTNode):
    key: str = ""
    value: str = ""
    comment: str = ""

    def to_string(self, indent: int = 0) -> str:
        pad = "    " * indent
        comm = f" # {self.comment}" if self.comment else ""
        return f"{pad}{self.key} = {self.value}{comm}"


@dataclass
class DirectiveNode(ASTNode):
    """
    Directives with repetitive keys like:
    monitor = ..., bind = ..., windowrulev2 = ..., exec-once = ..., bezier = ..., animation = ...
    """
    directive: str = ""
    value: str = ""
    comment: str = ""

    def to_string(self, indent: int = 0) -> str:
        pad = "    " * indent
        comm = f" # {self.comment}" if self.comment else ""
        return f"{pad}{self.directive} = {self.value}{comm}"


@dataclass
class SourceNode(ASTNode):
    """
    source = /path/to/included.conf
    """
    path: str = ""
    comment: str = ""

    def to_string(self, indent: int = 0) -> str:
        pad = "    " * indent
        comm = f" # {self.comment}" if self.comment else ""
        return f"{pad}source = {self.path}{comm}"


@dataclass
class SectionNode(ASTNode):
    """
    section_name {
        sub_items...
    }
    """
    name: str = ""
    body: List[ASTNode] = field(default_factory=list)
    comment: str = ""

    def to_string(self, indent: int = 0) -> str:
        pad = "    " * indent
        comm = f" # {self.comment}" if self.comment else ""
        lines = [f"{pad}{self.name} {{{comm}"]
        for child in self.body:
            lines.append(child.to_string(indent + 1))
        lines.append(f"{pad}}}")
        return "\n".join(lines)


@dataclass
class RawLineNode(ASTNode):
    raw: str = ""

    def to_string(self, indent: int = 0) -> str:
        pad = "    " * indent
        return f"{pad}{self.raw}"


@dataclass
class ConfigFileAST:
    file_path: str = ""
    nodes: List[ASTNode] = field(default_factory=list)

    def to_string(self) -> str:
        rendered = []
        for node in self.nodes:
            rendered.append(node.to_string(0))
        return "\n".join(rendered) + ("\n" if rendered and not rendered[-1].endswith("\n") else "")
