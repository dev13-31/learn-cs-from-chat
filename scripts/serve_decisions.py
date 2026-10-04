#!/usr/bin/env python3
"""
serve_decisions.py - Strictly Secure Localhost HTTP Server for CS Decisions
Serves the D:/gemini/CS decisions/ directory bound EXCLUSIVELY to 127.0.0.1 (localhost).
Zero network exposure: outside devices and public networks cannot access this server.
"""

import sys
import os
import socket
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Ensure UTF-8 output even on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DEFAULT_DIR = Path("D:/gemini/CS decisions")

def find_available_port(start_port=8080):
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
            port += 1
    return start_port

def run_server(port=None, directory=DEFAULT_DIR):
    if port is None:
        port = find_available_port(8080)

    target_dir = Path(directory).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(target_dir)

    # Strictly bind to 127.0.0.1 loopback interface
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)

    print("=" * 65)
    print("[SECURE] CS DECISIONS LOCAL VIEWER")
    print("=" * 65)
    print(f"Directory      : {target_dir}")
    print(f"Bound Address  : 127.0.0.1 (Strict Localhost Loopback Only)")
    print(f"Security Status: ZERO external network exposure")
    print(f"Access URL     : http://127.0.0.1:{port}/")
    print(f"                 http://localhost:{port}/")
    print("=" * 65)
    print("Press Ctrl+C to stop the server.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_server(p)
