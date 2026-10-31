"""
Unit tests for ProfileManager.
"""

import os
import shutil
import tempfile
import unittest
from hyprconf_manager.core.profile_manager import ProfileManager


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


if __name__ == "__main__":
    unittest.main()
