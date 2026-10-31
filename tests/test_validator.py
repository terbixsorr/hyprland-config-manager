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


    def test_wildcard_monitor_is_valid(self):
        conf = "monitor = ,preferred,auto,1\n"
        res = self.validator.validate_content(conf)
        self.assertTrue(res.is_valid, f"Expected wildcard monitor to be valid: {res.summary()}")

    def test_unclosed_quotes_detection(self):
        conf = 'bind = SUPER, Return, exec, "kitty --single-instance\n'
        res = self.validator.validate_content(conf)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("unclosed quote" in e.message.lower() for e in res.errors))

    def test_out_of_range_opacity(self):
        conf = "decoration {\n    active_opacity = 1.5\n}\n"
        res = self.validator.validate_content(conf)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("active_opacity" in e.message.lower() for e in res.errors))

    def test_negative_integer_rejection(self):
        conf = "general {\n    gaps_in = -4\n}\n"
        res = self.validator.validate_content(conf)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("negative" in e.message.lower() for e in res.errors))


if __name__ == "__main__":
    unittest.main()
