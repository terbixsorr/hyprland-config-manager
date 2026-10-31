"""
Unit tests for Hyprland AST Parser.
"""

import os
import unittest
from hyprconf_manager.core.parser import HyprlandParser
from hyprconf_manager.core.ast_nodes import (
    CommentNode,
    BlankLineNode,
    VariableNode,
    AssignmentNode,
    DirectiveNode,
    SourceNode,
    SectionNode,
)

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_configs")


class TestHyprlandParser(unittest.TestCase):
    def setUp(self):
        self.parser = HyprlandParser()

    def test_parse_comments_and_blanks(self):
        snippet = "# Header\n\n$mod = SUPER # Main modifier\n"
        ast = self.parser.parse_string(snippet)
        self.assertEqual(len(ast.nodes), 3)
        self.assertIsInstance(ast.nodes[0], CommentNode)
        self.assertEqual(ast.nodes[0].text, "Header")
        self.assertIsInstance(ast.nodes[1], BlankLineNode)
        self.assertIsInstance(ast.nodes[2], VariableNode)
        self.assertEqual(ast.nodes[2].name, "mod")
        self.assertEqual(ast.nodes[2].value, "SUPER")
        self.assertEqual(ast.nodes[2].comment, "Main modifier")

    def test_parse_sections_and_nested_sections(self):
        snippet = """
decoration {
    rounding = 8
    blur {
        enabled = true
        size = 4
    }
}
"""
        ast = self.parser.parse_string(snippet)
        sections = [n for n in ast.nodes if isinstance(n, SectionNode)]
        self.assertEqual(len(sections), 1)
        dec_sec = sections[0]
        self.assertEqual(dec_sec.name, "decoration")

        sub_sections = [n for n in dec_sec.body if isinstance(n, SectionNode)]
        self.assertEqual(len(sub_sections), 1)
        blur_sec = sub_sections[0]
        self.assertEqual(blur_sec.name, "blur")

        assignments = [n for n in blur_sec.body if isinstance(n, AssignmentNode)]
        self.assertEqual(len(assignments), 2)
        self.assertEqual(assignments[0].key, "enabled")
        self.assertEqual(assignments[0].value, "true")
        self.assertEqual(assignments[1].key, "size")
        self.assertEqual(assignments[1].value, "4")

    def test_parse_complex_file(self):
        path = os.path.join(SAMPLE_DIR, "complex_hyprland.conf")
        ast = self.parser.parse_file(path)
        self.assertGreater(len(ast.nodes), 10)

        # Check source directive
        sources = [n for n in ast.nodes if isinstance(n, SourceNode)]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].path, "~/.config/hypr/colors.conf")

        # Check monitors
        monitors = [n for n in ast.nodes if isinstance(n, DirectiveNode) and n.directive == "monitor"]
        self.assertEqual(len(monitors), 3)


if __name__ == "__main__":
    unittest.main()
