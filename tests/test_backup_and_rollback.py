"""
Unit tests for BackupManager.
"""

import os
import shutil
import tempfile
import unittest
from hyprconf_manager.core.backup_manager import BackupManager


class TestBackupManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.backup_mgr = BackupManager(backup_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_list_backup(self):
        content = "general { gaps_in = 5 }\n"
        entry = self.backup_mgr.create_backup(content, reason="Test snapshot")
        self.assertTrue(os.path.exists(entry.file_path))

        backups = self.backup_mgr.list_backups()
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].id, entry.id)
        self.assertEqual(backups[0].reason, "Test snapshot")

    def test_restore_backup(self):
        content = "general { gaps_in = 10 }\n"
        entry = self.backup_mgr.create_backup(content, reason="Initial")

        restore_target = os.path.join(self.temp_dir, "restored_hyprland.conf")
        ok, msg = self.backup_mgr.restore_backup(entry.id, restore_target)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(restore_target))

        with open(restore_target, "r") as f:
            self.assertEqual(f.read(), content)


if __name__ == "__main__":
    unittest.main()
