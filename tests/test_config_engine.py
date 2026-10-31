"""
Unit tests for HyprlandConfigEngine.
"""

import os
import unittest
from hyprconf_manager.core.config_engine import HyprlandConfigEngine

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_configs")


class TestConfigEngine(unittest.TestCase):
    def test_load_and_extract_default(self):
        engine = HyprlandConfigEngine()
        engine.load_file(os.path.join(SAMPLE_DIR, "default_hyprland.conf"))

        # Check extracted monitors
        self.assertEqual(len(engine.monitors), 2)
        self.assertEqual(engine.monitors[0].name, "DP-1")
        self.assertEqual(engine.monitors[0].resolution, "1920x1080")
        self.assertEqual(engine.monitors[0].refresh_rate, 144.0)

        # Check extracted window settings
        self.assertEqual(engine.windows.gaps_in, 5)
        self.assertEqual(engine.windows.gaps_out, 20)
        self.assertEqual(engine.windows.border_size, 2)
        self.assertEqual(engine.windows.rounding, 10)
        self.assertTrue(engine.windows.blur_enabled)
        self.assertEqual(engine.windows.blur_passes, 1)

        # Check extracted keybinds
        self.assertGreater(len(engine.keybinds), 5)
        q_bind = next((b for b in engine.keybinds if b.key == "Q"), None)
        self.assertIsNotNone(q_bind)
        self.assertEqual(q_bind.dispatcher, "exec")
        self.assertEqual(q_bind.arguments, "$terminal")

    def test_modify_and_sync_models(self):
        engine = HyprlandConfigEngine()
        engine.load_file(os.path.join(SAMPLE_DIR, "default_hyprland.conf"))

        # Modify gaps and border size
        engine.windows.gaps_in = 12
        engine.windows.border_size = 4
        engine.windows.rounding = 16

        candidate = engine.generate_candidate_config()
        self.assertIn("gaps_in = 12", candidate)
        self.assertIn("border_size = 4", candidate)
        self.assertIn("rounding = 16", candidate)


if __name__ == "__main__":
    unittest.main()
