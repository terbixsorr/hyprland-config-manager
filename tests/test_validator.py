"""
Unit tests for HyprlandValidator.
"""

import os
import unittest
from hyprconf_manager.core.validator import HyprlandValidator

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_configs")


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = HyprlandValidator()

    def test_valid_config(self):
        with open(os.path.join(SAMPLE_DIR, "default_hyprland.conf"), "r") as f:
            content = f.read()
        res = self.validator.validate_content(content)
        self.assertTrue(res.is_valid, f"Expected valid config, got errors: {res.summary()}")

    def test_invalid_config_detection(self):
        with open(os.path.join(SAMPLE_DIR, "invalid_hyprland.conf"), "r") as f:
            content = f.read()
        res = self.validator.validate_content(content)
        self.assertFalse(res.is_valid)
        self.assertGreater(len(res.errors), 0)

        error_msgs = [e.message for e in res.errors]
        # Should detect invalid scale and unclosed section
        self.assertTrue(any("scale" in m.lower() for m in error_msgs))
        self.assertTrue(any("unclosed" in m.lower() for m in error_msgs))


if __name__ == "__main__":
    unittest.main()
