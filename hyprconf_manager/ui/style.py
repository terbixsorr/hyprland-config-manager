"""
Custom styling for Hyprland Config Manager.
Provides modern dark obsidian and glassmorphic accents adhering to
Antigravity UI/UX Design Standards.
"""

CSS_STYLING = """
/* Hyprland Config Manager Modern Desktop Theme */

window.hypr-window {
    background-color: #0b0f19;
    color: #e2e8f0;
}

/* Sidebar navigation */
.hypr-sidebar {
    background-color: rgba(15, 23, 42, 0.75);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.hypr-sidebar-item {
    border-radius: 8px;
    padding: 8px 12px;
    margin: 2px 8px;
    transition: all 180ms ease-out;
}

.hypr-sidebar-item:hover {
    background-color: rgba(255, 255, 255, 0.05);
}

.hypr-sidebar-item:selected {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(168, 85, 247, 0.25));
    border: 1px solid rgba(168, 85, 247, 0.4);
    color: #ffffff;
}

/* Cards and surface panels */
.card, .adw-preferences-group {
    background-color: #111827;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

/* Metric / Stat badges */
.stat-card {
    background: linear-gradient(180deg, #161f30 0%, #0f172a 100%);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 12px;
    padding: 16px;
    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
}

.stat-value {
    font-size: 24px;
    font-weight: 800;
    color: #38bdf8;
    font-family: monospace;
}

.stat-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    font-weight: 600;
}

/* Status dots */
.status-dot-active {
    background-color: #10b981;
    border-radius: 9999px;
    min-width: 10px;
    min-height: 10px;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.8);
}

.status-dot-inactive {
    background-color: #f59e0b;
    border-radius: 9999px;
    min-width: 10px;
    min-height: 10px;
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.6);
}

.status-dot-error {
    background-color: #ef4444;
    border-radius: 9999px;
    min-width: 10px;
    min-height: 10px;
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.8);
}

/* Action buttons */
.btn-primary-apply {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: #ffffff;
    font-weight: 700;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 2px 10px rgba(79, 70, 229, 0.35);
    padding: 6px 16px;
}

.btn-primary-apply:hover {
    background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%);
    box-shadow: 0 4px 16px rgba(124, 58, 237, 0.5);
}

.btn-rollback {
    background-color: rgba(239, 68, 68, 0.15);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 8px;
    padding: 6px 14px;
}

.btn-rollback:hover {
    background-color: rgba(239, 68, 68, 0.25);
    border-color: rgba(239, 68, 68, 0.6);
}

/* Custom scrollbars */
scrollbar slider {
    background-color: rgba(148, 163, 184, 0.25);
    border-radius: 9999px;
    min-width: 6px;
    min-height: 6px;
}

scrollbar slider:hover {
    background-color: rgba(148, 163, 184, 0.45);
}
"""


def apply_custom_css():
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Gdk", "4.0")
        from gi.repository import Gtk, Gdk

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS_STYLING.encode("utf-8"))
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
    except Exception:
        pass
