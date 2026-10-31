"""
Unit tests for Keybind conflict detection.
"""

import unittest
from hyprconf_manager.core.validator import HyprlandValidator


class TestKeybindsConflicts(unittest.TestCase):
    def setUp(self):
        self.validator = HyprlandValidator()

    def test_conflict_warning_generated(self):
        config_with_conflict = """
$mainMod = SUPER
bind = $mainMod, Q, exec, kitty
bind = $mainMod, Q, exec, alacritty # Duplicate!
"""
        res = self.validator.validate_content(config_with_conflict)
        warnings = [w.message for w in res.warnings]
        self.assertTrue(any("conflicts with earlier binding" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
