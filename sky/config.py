import os
import socket
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(PROJECT_ROOT / ".env")

def is_internet_available(host: str = "8.8.8.8", port: int = 53, timeout: float = 1.5) -> bool:
    """Checks if there is an active internet connection by probing public DNS."""
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
        return True
    except OSError:
        pass
    # Secondary check with Cloudflare DNS
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("1.1.1.1", port))
        return True
    except OSError:
        return False

class GroqKeyManager:
    """Manages a pool of Groq API keys with automatic rotation and fallback."""

    def __init__(self):
        self._keys: List[str] = []
        self._current_index = 0
        self.reload_keys()

    def reload_keys(self):
        keys = []
        # Primary key
        k0 = os.getenv("GROQ_API_KEY", "").strip()
        if k0 and k0 != "your_groq_api_key_here":
            keys.append(k0)

        # Fallback numbered keys (GROQ_API_KEY1, GROQ_API_KEY2, ...)
        for i in range(1, 10):
            ki = os.getenv(f"GROQ_API_KEY{i}", "").strip()
            if ki and ki != "your_groq_api_key_here" and ki not in keys:
                keys.append(ki)

        # Catch any additional GROQ_API_KEY_* variants
        for k, v in os.environ.items():
            if k.startswith("GROQ_API_KEY") and v.strip() and v.strip() not in keys and v.strip() != "your_groq_api_key_here":
                keys.append(v.strip())

        self._keys = keys

    @property
    def current_key(self) -> str:
        if not self._keys:
            return ""
        return self._keys[self._current_index % len(self._keys)]

    def rotate_key(self) -> str:
        """Rotates to the next available key and returns it."""
        if len(self._keys) <= 1:
            return self.current_key
        prev_idx = self._current_index % len(self._keys)
        self._current_index = (self._current_index + 1) % len(self._keys)
        new_key = self.current_key
        print(f"\n[KeyManager] 🔄 Quota/Rate limit reached on Key #{prev_idx}. Switched to fallback Key #{self._current_index} ({new_key[:10]}...)")
        return new_key

    def count(self) -> int:
        return len(self._keys)

key_manager = GroqKeyManager()

def get_groq_api_key() -> str:
    return key_manager.current_key

def rotate_groq_api_key() -> str:
    return key_manager.rotate_key()

# LLM & Voice API Settings
GROQ_API_KEY = key_manager.current_key
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3").strip()

# Porcupine Wake Word Engine
PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY", "").strip()

# Wake Words
wake_words_raw = os.getenv("WAKE_WORDS", "hey sky,wake up sky,sky")
WAKE_WORDS = [w.strip().lower() for w in wake_words_raw.split(",") if w.strip()]

# TTS Setting
ENABLE_TTS = os.getenv("ENABLE_TTS", "true").lower() in ("true", "1", "yes")
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-GuyNeural").strip()

# Directories
DYNAMIC_TOOLS_DIR = PROJECT_ROOT / os.getenv("DYNAMIC_TOOLS_DIR", "sky/tools/dynamic")
DYNAMIC_TOOLS_DIR.mkdir(parents=True, exist_ok=True)

WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", str(PROJECT_ROOT / "workspace"))).resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

def validate_environment() -> tuple[bool, str]:
    """Check if mandatory environment variables are present."""
    if key_manager.count() == 0:
        return False, "GROQ_API_KEY is not set in .env! Please add your key to continue."
    return True, f"Environment configured with {key_manager.count()} Groq API key(s)."
