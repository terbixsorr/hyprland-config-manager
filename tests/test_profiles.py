"""
Unit tests for ProfileManager.
"""

import os
import shutil
import tempfile
import unittest
from hyprconf_manager.core.profile_manager import ProfileManager, validate_profile_dict
from hyprconf_manager.core.config_engine import HyprlandConfigEngine


class TestProfileManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.profile_mgr = ProfileManager(profiles_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_profiles_created(self):
        profiles = self.profile_mgr.list_profiles()
        self.assertIn("Gaming", profiles)
        self.assertIn("Work", profiles)
        self.assertIn("Laptop", profiles)
        self.assertIn("Minimal", profiles)
        self.assertIn("Streaming", profiles)

    def test_duplicate_and_rename_profile(self):
        ok = self.profile_mgr.duplicate_profile("Gaming", "MyGaming")
        self.assertTrue(ok)
        self.assertIn("MyGaming", self.profile_mgr.list_profiles())

        ok_ren = self.profile_mgr.rename_profile("MyGaming", "ProGaming")
        self.assertTrue(ok_ren)
        self.assertIn("ProGaming", self.profile_mgr.list_profiles())
        self.assertNotIn("MyGaming", self.profile_mgr.list_profiles())

    def test_validate_profile_dict_success(self):
        valid_profile = {
            "name": "Custom",
            "description": "Custom workflow",
            "windows": {
                "border_size": 2,
                "rounding": 8,
                "gaps_in": 5,
                "gaps_out": 10,
                "active_opacity": 0.95,
                "inactive_opacity": 0.85
            },
            "animations": {
                "enabled": True,
                "preset": "Smooth"
            },
            "input": {
                "kb_layout": "us,ru",
                "sensitivity": -0.2,
                "touchpad_tap_to_click": True
            }
        }
        is_valid, msg = validate_profile_dict(valid_profile)
        self.assertTrue(is_valid, f"Validation failed unexpectedly: {msg}")

    def test_validate_profile_dict_rejects_invalid_types_and_ranges(self):
        # 1. Non-dict root
        self.assertFalse(validate_profile_dict("not a dict")[0])
        self.assertFalse(validate_profile_dict([1, 2, 3])[0])

        # 2. Negative numeric fields
        inv_neg = {"windows": {"border_size": -5}}
        self.assertFalse(validate_profile_dict(inv_neg)[0])

        # 3. Opacity > 1.0 or < 0.0
        inv_op1 = {"windows": {"active_opacity": 1.5}}
        self.assertFalse(validate_profile_dict(inv_op1)[0])
        inv_op2 = {"windows": {"active_opacity": -0.1}}
        self.assertFalse(validate_profile_dict(inv_op2)[0])

        # 4. Sensitivity outside -1.0..1.0
        inv_sens = {"input": {"sensitivity": 2.5}}
        self.assertFalse(validate_profile_dict(inv_sens)[0])

        # 5. Invalid type for boolean
        inv_bool = {"animations": {"enabled": "yes"}}
        self.assertFalse(validate_profile_dict(inv_bool)[0])

    def test_apply_profile_data_to_config_engine(self):
        engine = HyprlandConfigEngine()
        profile_data = {
            "windows": {
                "border_size": 4,
                "rounding": 12,
                "gaps_in": 7,
                "gaps_out": 14,
                "active_opacity": 0.92,
                "inactive_opacity": 0.80
            },
            "animations": {
                "enabled": False,
                "preset": "Minimal"
            },
            "appearance": {
                "theme_name": "Tokyo Night",
                "col_active_border": "0xff7aa2f7"
            },
            "input": {
                "kb_layout": "us,ru",
                "kb_options": "grp:alt_shift_toggle",
                "sensitivity": -0.5,
                "touchpad_tap_to_click": False,
                "natural_scroll": True
            }
        }

        engine.apply_profile_data(profile_data)

        # Verify windows
        self.assertEqual(engine.windows.border_size, 4)
        self.assertEqual(engine.windows.rounding, 12)
        self.assertEqual(engine.windows.gaps_in, 7)
        self.assertEqual(engine.windows.gaps_out, 14)
        self.assertEqual(engine.windows.active_opacity, 0.92)

        # Verify animations
        self.assertFalse(engine.animations.enabled)
        self.assertEqual(engine.animations.preset, "Minimal")

        # Verify appearance
        self.assertEqual(engine.appearance.theme_name, "Tokyo Night")
        self.assertEqual(engine.appearance.col_active_border, "0xff7aa2f7")

        # Verify input
        self.assertEqual(engine.input_cfg.kb_layout, "us,ru")
        self.assertEqual(engine.input_cfg.kb_options, "grp:alt_shift_toggle")
        self.assertEqual(engine.input_cfg.sensitivity, -0.5)
        self.assertFalse(engine.input_cfg.touchpad_tap_to_click)
        self.assertTrue(engine.input_cfg.natural_scroll)


if __name__ == "__main__":
    unittest.main()
