#!/usr/bin/env python3
"""
Bullpen Web UI

Start the web server:
    python bullpen_web.py [port]

Examples:
    python bullpen_web.py        # Default port 8000
    python bullpen_web.py 3000   # Custom port
"""
import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from web.app import app

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print("Starting Bullpen Web UI...")
    print(f"Open http://localhost:{port} in your browser")
    print("Press Ctrl+C to stop\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
