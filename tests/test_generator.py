"""
Unit tests for Hyprland AST Generator and Diff Engine.
"""

import unittest
from hyprconf_manager.core.parser import HyprlandParser
from hyprconf_manager.core.generator import HyprlandGenerator


class TestHyprlandGenerator(unittest.TestCase):
    def test_roundtrip_preservation(self):
        original = (
            "# My personal config\n"
            "$terminal = kitty\n"
            "\n"
            "general {\n"
            "    gaps_in = 5\n"
            "    border_size = 2 # custom border\n"
            "}\n"
        )
        parser = HyprlandParser()
        ast = parser.parse_string(original)
        generated = HyprlandGenerator.generate(ast)
        self.assertEqual(original.strip(), generated.strip())

    def test_diff_computation(self):
        old_cfg = "general {\n    gaps_in = 5\n}\n"
        new_cfg = "general {\n    gaps_in = 10\n}\n"
        diff = HyprlandGenerator.compute_diff(old_cfg, new_cfg)
        self.assertIn("-    gaps_in = 5", diff)
        self.assertIn("+    gaps_in = 10", diff)
        added, removed = HyprlandGenerator.get_diff_stats(diff)
        self.assertEqual(added, 1)
        self.assertEqual(removed, 1)


if __name__ == "__main__":
    unittest.main()
