"""
Hyprland Config Manager - Standalone Windows Demo Launcher
Serves the local interactive GUI and launches it in native application window mode.
"""

import os
import sys
import socket
import subprocess
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

def find_free_port(start_port=5050):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return 5050

def run_server(port, root_dir):
    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root_dir, **kwargs)

        def log_message(self, format, *args):
            # Suppress normal access logs for clean console
            pass

    server = HTTPServer(('127.0.0.1', port), QuietHandler)
    server.serve_forever()

def launch_app_window(url):
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe")
    ]
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe")
    ]

    for p in edge_paths:
        if os.path.exists(p):
            try:
                subprocess.Popen([p, f"--app={url}", "--window-size=1280,860"])
                return
            except Exception:
                pass

    for p in chrome_paths:
        if os.path.exists(p):
            try:
                subprocess.Popen([p, f"--app={url}", "--window-size=1280,860"])
                return
            except Exception:
                pass

    # Fallback to default browser
    webbrowser.open(url)

def main():
    demo_dir = os.path.dirname(os.path.abspath(__file__))
    port = find_free_port(5050)
    url = f"http://127.0.0.1:{port}/"

    server_thread = threading.Thread(target=run_server, args=(port, demo_dir), daemon=True)
    server_thread.start()
    time.sleep(0.3)

    print("==============================================================")
    print("  Hyprland Config Manager — Windows Interactive Demo")
    print("==============================================================")
    print(f"  Local Demo Server active at: {url}")
    print("  Launching native desktop application window...")
    print("  Press Ctrl+C to stop the demo server.")
    print("==============================================================")

    launch_app_window(url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDemo stopped.")

if __name__ == "__main__":
    main()
