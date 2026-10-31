"""
Main entry point for Hyprland Config Manager.
Supports both native GTK4/Libadwaita GUI mode and fast CLI operations.
"""

import argparse
import os
import sys

from .core.config_engine import HyprlandConfigEngine
from .core.backup_manager import BackupManager
from .core.validator import HyprlandValidator
from .core.hyprctl import HyprctlClient
from .core.profile_manager import ProfileManager
from .core.safe_apply import SafeApplyPipeline
from .core.generator import HyprlandGenerator

VERSION = "1.0.0"


def main():
    parser = argparse.ArgumentParser(
        prog="hyprland-config-manager",
        description="Modern native GUI & CLI configuration manager for Hyprland on Arch Linux"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-c", "--config", help="Path to custom hyprland.conf", default=None)
    parser.add_argument("--validate", action="store_true", help="Validate hyprland.conf syntax and integrity")
    parser.add_argument("--status", action="store_true", help="Print Hyprland compositor runtime status")
    parser.add_argument("--backup", nargs="?", const="Manual CLI backup", help="Create an immediate backup snapshot")
    parser.add_argument("--rollback", nargs="?", const="", help="Restore the latest (or specified) backup")
    parser.add_argument("--list-backups", action="store_true", help="List all recorded configuration backups")
    parser.add_argument("--profiles", action="store_true", help="List all available configuration profiles")
    parser.add_argument("--activate-profile", help="Activate a specific configuration profile")
    parser.add_argument("--diff", action="store_true", help="Show diff between current disk config and candidate model")
    parser.add_argument("--cli", action="store_true", help="Force CLI mode even if display server is available")

    args, unknown = parser.parse_known_args()

    engine = HyprlandConfigEngine(config_path=args.config)
    backup_mgr = BackupManager()
    validator = HyprlandValidator()
    hyprctl = HyprctlClient()
    profile_mgr = ProfileManager()
    safe_apply = SafeApplyPipeline(backup_mgr, validator, hyprctl)

    # 1. Validation mode
    if args.validate:
        engine.load_file()
        content = engine.generate_candidate_config()
        res = validator.validate_content(content)
        print(res.summary())
        sys.exit(0 if res.is_valid else 1)

    # 2. Status mode
    if args.status:
        st = hyprctl.get_status()
        print("=== Hyprland Status ===")
        print(f"Running:      {st.is_running}")
        print(f"Version:      {st.version}")
        print(f"Monitors:     {st.monitors_count}")
        print(f"Workspaces:   {st.workspaces_count}")
        if st.active_window_class:
            print(f"Active Win:   {st.active_window_class} - {st.active_window_title}")
        print(f"Config path:  {engine.config_path}")
        print(f"Active Prof:  {profile_mgr.get_active_profile()}")
        sys.exit(0)

    # 3. Backup mode
    if args.backup is not None:
        engine.load_file()
        entry = backup_mgr.create_backup(engine.raw_original_content, reason=args.backup)
        print(f"Created backup snapshot [{entry.id}] at: {entry.file_path}")
        sys.exit(0)

    # 4. Rollback mode
    if args.rollback is not None:
        backup_id = args.rollback if args.rollback else None
        ok, msg = safe_apply.rollback(engine, backup_id=backup_id)
        print(msg)
        sys.exit(0 if ok else 1)

    # 5. List backups
    if args.list_backups:
        backups = backup_mgr.list_backups()
        print(f"Recorded backups ({len(backups)}):")
        for b in backups:
            print(f"  • [{b.id}] {b.timestamp} - {b.reason} ({b.size_bytes} bytes)")
        sys.exit(0)

    # 6. Profiles listing
    if args.profiles:
        profs = profile_mgr.list_profiles()
        active = profile_mgr.get_active_profile()
        print("Available profiles:")
        for p in profs:
            mark = " * (ACTIVE)" if p == active else ""
            data = profile_mgr.load_profile(p) or {}
            desc = data.get("description", "")
            print(f"  • {p}{mark}: {desc}")
        sys.exit(0)

    # 7. Activate profile
    if args.activate_profile:
        name = args.activate_profile
        data = profile_mgr.load_profile(name)
        if not data:
            print(f"Error: Profile '{name}' not found.")
            sys.exit(1)
        engine.load_file()
        backup_mgr.create_backup(engine.raw_original_content, reason=f"Backup before activating profile '{name}'")
        if "windows" in data:
            for k, v in data["windows"].items():
                if hasattr(engine.windows, k):
                    setattr(engine.windows, k, v)
        if "animations" in data:
            if "enabled" in data["animations"]:
                engine.animations.enabled = data["animations"]["enabled"]
            if "preset" in data["animations"]:
                engine.animations.preset = data["animations"]["preset"]
        if "appearance" in data and "theme_name" in data["appearance"]:
            engine.appearance.theme_name = data["appearance"]["theme_name"]

        res = safe_apply.apply(engine, reason=f"Activated profile '{name}'")
        if res.success:
            profile_mgr.set_active_profile(name)
            print(f"Successfully activated profile '{name}'.")
            sys.exit(0)
        else:
            print(f"Failed to activate profile: {res.message}")
            if res.details:
                print(res.details)
            sys.exit(1)

    # 8. Diff mode
    if args.diff:
        engine.load_file()
        current_disk = engine.raw_original_content
        candidate = engine.generate_candidate_config()
        diff = HyprlandGenerator.compute_diff(current_disk, candidate, "disk_config", "model_candidate")
        if diff:
            print(diff)
        else:
            print("No differences found between disk config and candidate model.")
        sys.exit(0)

    # 9. Launch Native GUI
    try:
        from .ui.app import HyprlandConfigApp
        app = HyprlandConfigApp(config_path=args.config)
        sys.exit(app.run([sys.argv[0]] + unknown))
    except (ImportError, Exception) as e:
        print(f"[Hyprland Config Manager] Could not initialize graphical interface: {e}")
        print("Falling back to CLI info mode. Run with --help for command line options.")
        st = hyprctl.get_status()
        print(f"Hyprland Status: {'Running' if st.is_running else 'Offline'} ({st.version})")
        sys.exit(0)


if __name__ == "__main__":
    main()
