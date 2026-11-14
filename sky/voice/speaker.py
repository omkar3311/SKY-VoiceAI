import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import asyncio
import io
import re
import subprocess
import threading
from pathlib import Path
from typing import Optional, Callable
from sky.config import ENABLE_TTS, TTS_VOICE, PROJECT_ROOT

class HumanSpeaker:
    """Lifelike Neural Text-to-Speech engine for natural human conversations."""

    def __init__(self, voice: str = TTS_VOICE):
        self.enabled = ENABLE_TTS
        self.is_muted = False
        self.is_speaking = False
        self.voice = voice  # Standard lifelike male voice (en-US-GuyNeural)
        self._lock = threading.Lock()
        self._pygame_initialized = False

    def _ensure_pygame(self):
        if not self._pygame_initialized:
            try:
                import pygame
                os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
                pygame.mixer.init()
                self._pygame_initialized = True
            except Exception:
                pass

    def mute(self):
        """Mutes speech output so only text displays on the terminal."""
        self.is_muted = True

    def unmute(self):
        """Unmutes speech output so Sky speaks aloud again."""
        self.is_muted = False

    def clean_text_for_speech(self, text: str) -> str:
        """Strip robotic technical syntax and formatting for natural human speech."""
        if not text:
            return ""

        # Remove code blocks entirely, replace with natural phrase
        text = re.sub(r"```[\w]*\n[\s\S]*?```", " I've created the code for you. ", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove markdown symbols, headers, links, bullets
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"(\*\*|\*|__|_)", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"^[\-\*•]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"✅|❌|⚡|🚀|🤖|💻|📁|🔊|🔇", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    async def _stream_and_play(self, clean_text: str, on_start: Optional[Callable] = None):
        """Streams audio chunks from edge-tts directly to ffplay for instant speech start."""
        started = False
        try:
            import edge_tts
            communicate = edge_tts.Communicate(clean_text, self.voice)
            proc = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-"],
                stdin=subprocess.PIPE
            )
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    if not started:
                        started = True
                        if on_start:
                            try:
                                on_start()
                            except Exception:
                                pass
                    try:
                        proc.stdin.write(chunk["data"])
                        proc.stdin.flush()
                    except (BrokenPipeError, OSError):
                        break
            try:
                proc.stdin.close()
            except Exception:
                pass
            proc.wait()
            if not started and on_start:
                on_start()
        except Exception:
            # Fallback if ffplay or edge-tts streaming fails
            if not started and on_start:
                try:
                    on_start()
                except Exception:
                    pass
            self._fallback_pyttsx3(clean_text)

    def _fallback_pyttsx3(self, text: str):
        """Fallback to local offline TTS if edge-tts is unavailable."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass

    def _fallback_pyttsx3_upset(self, text: str):
        """Fallback to local offline TTS with a slower, upset tone."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 125)  # Slower, disappointed/upset cadence
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass

    def speak_no_internet(self, on_start: Optional[Callable] = None, blocking: bool = True):
        """
        Speaks the upset hardcoded no-internet message using pre-rendered offline audio assets
        or fallback pyttsx3 with a slow, upset tone. Works with 0% internet connection.
        """
        if not self.enabled or self.is_muted:
            if on_start:
                try:
                    on_start()
                except Exception:
                    pass
            return

        def _do_play():
            with self._lock:
                self.is_speaking = True
                try:
                    if on_start:
                        try:
                            on_start()
                        except Exception:
                            pass

                    # Try playing the pre-rendered upset asset file (works 100% offline)
                    asset_wav = PROJECT_ROOT / "sky" / "voice" / "assets" / "no_internet.wav"
                    asset_mp3 = PROJECT_ROOT / "sky" / "voice" / "assets" / "no_internet.mp3"
                    target = asset_wav if asset_wav.exists() else (asset_mp3 if asset_mp3.exists() else None)

                    played = False
                    if target and target.exists():
                        try:
                            proc = subprocess.run(
                                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(target)],
                                timeout=15
                            )
                            played = (proc.returncode == 0)
                        except Exception:
                            played = False

                        if not played:
                            try:
                                self._ensure_pygame()
                                import pygame
                                pygame.mixer.music.load(str(target))
                                pygame.mixer.music.play()
                                while pygame.mixer.music.get_busy():
                                    pygame.time.Clock().tick(20)
                                played = True
                            except Exception:
                                played = False

                    if not played:
                        self._fallback_pyttsx3_upset(
                            "Ugh... Omkar, I don't have an internet connection right now! I really can't do anything without Wi-Fi... Please connect me to the internet!"
                        )
                finally:
                    self.is_speaking = False

        if blocking:
            _do_play()
        else:
            threading.Thread(target=_do_play, daemon=True).start()

    def speak_reconnected(self, on_start: Optional[Callable] = None, blocking: bool = True):
        """
        Speaks the enthusiastic reconnected message ('Yahoo! Now I'm feeling the power in my veins!').
        Uses pre-rendered local asset for instant playback.
        """
        if not self.enabled or self.is_muted:
            if on_start:
                try:
                    on_start()
                except Exception:
                    pass
            return

        def _do_play():
            with self._lock:
                self.is_speaking = True
                try:
                    if on_start:
                        try:
                            on_start()
                        except Exception:
                            pass

                    asset_wav = PROJECT_ROOT / "sky" / "voice" / "assets" / "reconnected.wav"
                    asset_mp3 = PROJECT_ROOT / "sky" / "voice" / "assets" / "reconnected.mp3"
                    target = asset_wav if asset_wav.exists() else (asset_mp3 if asset_mp3.exists() else None)

                    played = False
                    if target and target.exists():
                        try:
                            proc = subprocess.run(
                                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(target)],
                                timeout=15
                            )
                            played = (proc.returncode == 0)
                        except Exception:
                            played = False

                        if not played:
                            try:
                                self._ensure_pygame()
                                import pygame
                                pygame.mixer.music.load(str(target))
                                pygame.mixer.music.play()
                                while pygame.mixer.music.get_busy():
                                    pygame.time.Clock().tick(20)
                                played = True
                            except Exception:
                                played = False

                    if not played:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            self._stream_and_play(
                                "Yahoo! Internet is back! Now I'm feeling the power in my veins! Ready for your commands, Omkar!",
                                None
                            )
                        )
                        loop.close()
                except Exception:
                    self._fallback_pyttsx3(
                        "Yahoo! Internet is back! Now I am feeling the power in my veins!"
                    )
                finally:
                    self.is_speaking = False

        if blocking:
            _do_play()
        else:
            threading.Thread(target=_do_play, daemon=True).start()

    def speak(self, text: str, on_start: Optional[Callable] = None, blocking: bool = True):
        """
        Speak given text aloud in a natural, human voice.
        on_start callback is invoked the exact millisecond audio playback starts.
        """
        if not self.enabled or self.is_muted:
            if on_start:
                try:
                    on_start()
                except Exception:
                    pass
            return

        clean = self.clean_text_for_speech(text)
        if not clean:
            if on_start:
                try:
                    on_start()
                except Exception:
                    pass
            return

        def _do_speak():
            with self._lock:
                self.is_speaking = True
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._stream_and_play(clean, on_start))
                    loop.close()
                except Exception:
                    if on_start:
                        try:
                            on_start()
                        except Exception:
                            pass
                    self._fallback_pyttsx3(clean)
                finally:
                    self.is_speaking = False

        if blocking:
            _do_speak()
        else:
            threading.Thread(target=_do_speak, daemon=True).start()

speaker = HumanSpeaker()
