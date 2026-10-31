"""
Backup Manager for Hyprland configuration.
Creates timestamped snapshots before applies and profile switches,
manages retention, provides diffs, and handles instant rollback.
"""

import json
import os
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class BackupEntry:
    id: str
    filename: str
    timestamp: str
    reason: str
    size_bytes: int
    file_path: str


class BackupManager:
    def __init__(self, backup_dir: Optional[str] = None):
        if backup_dir:
            self.backup_dir = backup_dir
        else:
            xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            self.backup_dir = os.path.join(xdg_config, "hyprland-config-manager", "backups")
        
        os.makedirs(self.backup_dir, exist_ok=True)
        self.index_file = os.path.join(self.backup_dir, "index.json")

    def _load_index(self) -> List[dict]:
        if not os.path.exists(self.index_file):
            return []
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_index(self, entries: List[dict]):
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def create_backup(self, content_or_path: str, reason: str = "Auto backup before Apply") -> BackupEntry:
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"hyprland_{timestamp_str}.conf"
        target_path = os.path.join(self.backup_dir, filename)

        if os.path.exists(content_or_path) and os.path.isfile(content_or_path):
            shutil.copy2(content_or_path, target_path)
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                size_bytes = len(f.read().encode("utf-8"))
        else:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content_or_path)
            size_bytes = len(content_or_path.encode("utf-8"))

        entry = BackupEntry(
            id=timestamp_str,
            filename=filename,
            timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
            reason=reason,
            size_bytes=size_bytes,
            file_path=target_path
        )

        entries = self._load_index()
        entries.insert(0, asdict(entry))
        self._save_index(entries)
        self.prune_old_backups(keep_max=30)
        return entry

    def list_backups(self) -> List[BackupEntry]:
        entries = self._load_index()
        result = []
        for e in entries:
            # Check if file still exists on disk
            if os.path.exists(e.get("file_path", "")):
                result.append(BackupEntry(**e))
        return result

    def get_latest_backup(self) -> Optional[BackupEntry]:
        backups = self.list_backups()
        return backups[0] if backups else None

    def get_backup_content(self, backup_id: str) -> Optional[str]:
        for b in self.list_backups():
            if b.id == backup_id:
                try:
                    with open(b.file_path, "r", encoding="utf-8", errors="replace") as f:
                        return f.read()
                except Exception:
                    return None
        return None

    def restore_backup(self, backup_id: str, target_config_path: str) -> Tuple[bool, str]:
        for b in self.list_backups():
            if b.id == backup_id:
                try:
                    os.makedirs(os.path.dirname(os.path.abspath(target_config_path)), exist_ok=True)
                    shutil.copy2(b.file_path, target_config_path)
                    return True, f"Successfully restored backup from {b.timestamp}"
                except Exception as e:
                    return False, f"Failed to restore backup: {str(e)}"
        return False, f"Backup {backup_id} not found"

    def delete_backup(self, backup_id: str) -> bool:
        entries = self._load_index()
        new_entries = []
        deleted = False
        for e in entries:
            if e.get("id") == backup_id:
                deleted = True
                fp = e.get("file_path", "")
                if os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
            else:
                new_entries.append(e)

        if deleted:
            self._save_index(new_entries)
        return deleted

    def prune_old_backups(self, keep_max: int = 30):
        entries = self._load_index()
        if len(entries) > keep_max:
            to_remove = entries[keep_max:]
            entries = entries[:keep_max]
            for r in to_remove:
                fp = r.get("file_path", "")
                if os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
            self._save_index(entries)
