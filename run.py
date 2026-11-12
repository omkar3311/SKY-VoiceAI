#!/usr/bin/env python3
"""
Sky AI - Main Entry Point
Dual-Agent Autonomous Desktop Assistant (Executor + Toolbuilder)
"""

import os
import sys
from pathlib import Path

# Fix Ubuntu + Conda C++ dynamic library priority if needed
system_libstdcxx = "/usr/lib/x86_64-linux-gnu/libstdc++.so.6"
if os.path.exists(system_libstdcxx) and "LD_PRELOAD" not in os.environ:
    os.environ["LD_PRELOAD"] = system_libstdcxx
    # Re-exec to apply LD_PRELOAD before C extensions load
    try:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from sky.cli import main

if __name__ == "__main__":
    main()
