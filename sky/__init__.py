"""
Sky AI - Autonomous Dual-Agent Desktop Assistant
Executor + Toolbuilder multi-agent architecture using LangChain, LangGraph, and Groq.
"""

import os
import ctypes

# Automatically load system C++ standard library if present to prevent conda library conflicts with PortAudio/JACK
system_libstdcxx = "/usr/lib/x86_64-linux-gnu/libstdc++.so.6"
if os.path.exists(system_libstdcxx):
    try:
        ctypes.CDLL(system_libstdcxx, mode=ctypes.RTLD_GLOBAL)
    except Exception:
        pass

__version__ = "1.0.0"
__author__ = "Omkar"
