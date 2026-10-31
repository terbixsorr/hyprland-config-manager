"""
Safe Apply & Rollback Pipeline for Hyprland configuration.
Implements the atomic transactional flow:
Current config -> Backup -> Generate -> Validate -> Permission-preserving Atomic Apply -> Hyprland Reload -> Verify.
If compositor reload fails, performs an audited rollback with post-restore verification.
"""

import os
import shutil
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from .config_engine import HyprlandConfigEngine
from .backup_manager import BackupManager, BackupEntry
from .validator import HyprlandValidator, ValidationResult, ValidationError
from .hyprctl import HyprctlClient, HyprlandStatus


@dataclass
class ApplyResult:
    success: bool
    message: str
    backup_created: Optional[BackupEntry] = None
    validation_result: Optional[ValidationResult] = None
    rollback_performed: bool = False
    details: str = ""


class SafeApplyPipeline:
    def __init__(self, backup_manager: Optional[BackupManager] = None,
                 validator: Optional[HyprlandValidator] = None,
                 hyprctl_client: Optional[HyprctlClient] = None):
        self.backup_mgr = backup_manager or BackupManager()
        self.validator = validator or HyprlandValidator()
        self.hyprctl = hyprctl_client or HyprctlClient()

    def apply(self, engine: HyprlandConfigEngine, reason: str = "User applied settings via GUI") -> ApplyResult:
        config_path = engine.config_path

        # Step 1: Read current config on disk (or create empty if missing)
        current_disk_content = ""
        orig_stat = None
        if os.path.exists(config_path):
            try:
                orig_stat = os.stat(config_path)
                with open(config_path, "r", encoding="utf-8", errors="replace") as f:
                    current_disk_content = f.read()
            except Exception as e:
                return ApplyResult(
                    success=False,
                    message=f"Cannot read existing configuration file: {e}"
                )
        else:
            current_disk_content = engine._get_default_template()

        # Step 2: Create Backup
        backup_entry = self.backup_mgr.create_backup(current_disk_content, reason=reason)

        # Step 3: Generate candidate config
        try:
            candidate_text = engine.generate_candidate_config()
        except Exception as e:
            return ApplyResult(
                success=False,
                message=f"Failed to generate configuration AST: {e}",
                backup_created=backup_entry
            )

        # Step 4: Validate candidate config
        val_res = self.validator.validate_content(candidate_text)
        if not val_res.is_valid:
            return ApplyResult(
                success=False,
                message="Configuration validation failed. Changes were NOT applied to avoid broken desktop.",
                backup_created=backup_entry,
                validation_result=val_res,
                details=val_res.summary()
            )

        # Step 5: Permission-preserving atomic write to disk
        tmp_path = f"{config_path}.tmp"
        try:
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(candidate_text)
                f.flush()
                os.fsync(f.fileno())

            # Preserve original permissions and ownership
            if orig_stat is not None:
                try:
                    os.chmod(tmp_path, orig_stat.st_mode)
                except Exception:
                    pass
                if hasattr(os, "chown") and os.name != "nt":
                    try:
                        os.chown(tmp_path, orig_stat.st_uid, orig_stat.st_gid)
                    except (PermissionError, OSError):
                        pass

            # Atomic replacement
            if os.name == "nt":
                if os.path.exists(config_path):
                    os.replace(tmp_path, config_path)
                else:
                    os.rename(tmp_path, config_path)
            else:
                os.replace(tmp_path, config_path)
            
            engine.raw_original_content = candidate_text
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return ApplyResult(
                success=False,
                message=f"Failed to write configuration file: {e}",
                backup_created=backup_entry
            )

        # Step 6: If Hyprland is active, reload and verify
        status = self.hyprctl.get_status()
        if status.is_running:
            reload_ok, reload_msg = self.hyprctl.reload()
            if not reload_ok:
                # AUTOMATIC ROLLBACK TRIGGERED!
                rollback_ok, rollback_msg = self.backup_mgr.restore_backup(backup_entry.id, config_path)
                
                # Verify that restored file exists and reload compositor
                file_restored = rollback_ok and os.path.exists(config_path) and os.path.getsize(config_path) > 0
                post_reload_ok = False
                post_reload_msg = ""
                if file_restored:
                    engine.load_file(config_path)
                    post_reload_ok, post_reload_msg = self.hyprctl.reload()

                details = (
                    f"Compositor error: {reload_msg}\n"
                    f"Rollback file restoration: {rollback_msg}\n"
                    f"Rollback reload verification: {'Success' if post_reload_ok else 'Failed'} ({post_reload_msg})"
                )

                return ApplyResult(
                    success=False,
                    message="Hyprland rejected the configuration! Automatic rollback was executed.",
                    backup_created=backup_entry,
                    rollback_performed=True,
                    details=details
                )

            return ApplyResult(
                success=True,
                message="Configuration applied and Hyprland reloaded successfully!",
                backup_created=backup_entry,
                validation_result=val_res,
                details=reload_msg
            )
        else:
            return ApplyResult(
                success=True,
                message="Configuration saved and verified. (Hyprland is not currently running)",
                backup_created=backup_entry,
                validation_result=val_res,
                details="File written successfully to " + config_path
            )

    def rollback(self, engine: HyprlandConfigEngine, backup_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Restores previous backup and reloads compositor with complete post-verification.
        """
        if not backup_id:
            latest = self.backup_mgr.get_latest_backup()
            if not latest:
                return False, "No backups available to rollback to."
            backup_id = latest.id

        ok, msg = self.backup_mgr.restore_backup(backup_id, engine.config_path)
        if not ok:
            return False, msg

        # Verify restored file on disk
        if not os.path.exists(engine.config_path) or os.path.getsize(engine.config_path) == 0:
            return False, f"Restored file at {engine.config_path} is missing or empty."

        # Reload engine state from restored file
        engine.load_file(engine.config_path)

        # If Hyprland is active, reload it and verify
        if self.hyprctl.get_status().is_running:
            r_ok, r_msg = self.hyprctl.reload()
            if not r_ok:
                return False, f"Restored backup, but Hyprland reload reported an issue: {r_msg}"
            return True, f"{msg}. Hyprland reloaded: {r_msg}"

        return True, f"{msg}. (Hyprland is offline)"
