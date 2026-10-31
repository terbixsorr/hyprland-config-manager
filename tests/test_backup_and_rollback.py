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

    def test_rapid_backups_unique_timestamps_no_overwrite(self):
        """Test that rapid backup creation in the same second never collides or overwrites."""
        created_entries = []
        for i in range(10):
            entry = self.backup_mgr.create_backup(f"# Snapshot {i}\n", reason=f"Rapid test {i}")
            created_entries.append(entry)

        # All IDs and file paths must be strictly unique
        ids = [e.id for e in created_entries]
        files = [e.file_path for e in created_entries]
        self.assertEqual(len(ids), len(set(ids)), "Backup IDs collided!")
        self.assertEqual(len(files), len(set(files)), "Backup file paths collided!")

        # All files must physically exist on disk
        for f in files:
            self.assertTrue(os.path.exists(f))

        # Index must report all 10 snapshots
        backups = self.backup_mgr.list_backups()
        self.assertEqual(len(backups), 10)

    def test_index_self_healing_from_disk(self):
        """Test that if index.json is deleted or corrupted, BackupManager recovers files from disk."""
        entry1 = self.backup_mgr.create_backup("config 1", reason="One")
        entry2 = self.backup_mgr.create_backup("config 2", reason="Two")

        # Corrupt / delete index.json
        index_file = os.path.join(self.temp_dir, "index.json")
        with open(index_file, "w") as f:
            f.write("INVALID JSON {[[")

        # Re-initialize BackupManager
        healed_mgr = BackupManager(backup_dir=self.temp_dir)
        backups = healed_mgr.list_backups()
        self.assertEqual(len(backups), 2)
        recovered_ids = [b.id for b in backups]
        self.assertIn(entry1.id, recovered_ids)
        self.assertIn(entry2.id, recovered_ids)


if __name__ == "__main__":
    unittest.main()
