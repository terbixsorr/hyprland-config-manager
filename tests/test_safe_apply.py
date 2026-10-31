"""
Unit tests for SafeApplyPipeline.
"""

import os
import shutil
import tempfile
import unittest
from hyprconf_manager.core.config_engine import HyprlandConfigEngine
from hyprconf_manager.core.backup_manager import BackupManager
from hyprconf_manager.core.validator import HyprlandValidator
from hyprconf_manager.core.hyprctl import HyprctlClient, HyprlandStatus
from hyprconf_manager.core.safe_apply import SafeApplyPipeline


class MockHyprctlClient(HyprctlClient):
    def __init__(self, is_running=True, reload_should_fail=False):
        super().__init__()
        self._mock_running = is_running
        self._reload_should_fail = reload_should_fail

    def get_status(self) -> HyprlandStatus:
        return HyprlandStatus(
            is_running=self._mock_running,
            version="Hyprland v0.41.0 (mock)"
        )

    def reload(self):
        if self._reload_should_fail:
            return False, "hyprctl: config error on line 42"
        return True, "ok"


class TestSafeApply(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "hyprland.conf")
        self.backup_mgr = BackupManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        self.validator = HyprlandValidator()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_safe_apply_success(self):
        engine = HyprlandConfigEngine(config_path=self.config_path)
        engine.load_from_string("general { gaps_in = 5 }\n", file_path=self.config_path)
        engine.save()

        mock_hypr = MockHyprctlClient(is_running=True, reload_should_fail=False)
        pipeline = SafeApplyPipeline(self.backup_mgr, self.validator, mock_hypr)

        engine.windows.gaps_in = 8
        res = pipeline.apply(engine, reason="Testing apply")
        self.assertTrue(res.success)
        self.assertIsNotNone(res.backup_created)

        with open(self.config_path, "r") as f:
            self.assertIn("gaps_in = 8", f.read())

    def test_safe_apply_auto_rollback_on_failure(self):
        original_content = "general { gaps_in = 5 }\n"
        with open(self.config_path, "w") as f:
            f.write(original_content)

        engine = HyprlandConfigEngine(config_path=self.config_path)
        engine.load_file()

        mock_hypr = MockHyprctlClient(is_running=True, reload_should_fail=True)
        pipeline = SafeApplyPipeline(self.backup_mgr, self.validator, mock_hypr)

        engine.windows.gaps_in = 99
        res = pipeline.apply(engine, reason="Testing broken reload")

        self.assertFalse(res.success)
        self.assertTrue(res.rollback_performed)

        # File on disk should have rolled back to original_content!
        with open(self.config_path, "r") as f:
            self.assertEqual(f.read(), original_content)


if __name__ == "__main__":
    unittest.main()
