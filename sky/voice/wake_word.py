import os
import re
import sys
import time
import random
from typing import Callable, Optional, Tuple
from sky.config import PICOVOICE_ACCESS_KEY, WAKE_WORDS
from sky.voice.listener import AudioListener
from sky.voice.speaker import speaker

STOP_PHRASES = [
    "call it a day",
    "call it day",
    "sky stop",
    "stop sky",
    "stop",
    "take a rest",
    "take rest",
    "rest",
    "shut down sky",
    "shutdown sky",
    "shut down",
    "shutdown",
    "turn off",
    "goodnight",
    "good night",
    "bye sky",
    "goodbye sky",
    "exit",
    "quit"
]

PC_SLEEP_PHRASES = [
    "go to sleep",
    "put pc to sleep",
    "put laptop to sleep",
    "put the pc to sleep",
    "put the laptop to sleep",
    "pc sleep",
    "laptop sleep",
    "sleep pc",
    "sleep laptop",
    "system sleep",
    "suspend pc",
    "suspend laptop",
    "suspend",
    "sleep"
]

FAREWELL_MESSAGES = [
    "Alright Omkar, calling it a day! Have a great rest.",
    "Resting now Omkar. Catch you later!",
    "Sky is resting now Omkar. Call me anytime you need me.",
    "Shutting down for now. Have a wonderful day Omkar!",
    "Alright Omkar, taking a rest. See you soon!"
]

MUTE_PHRASES = [
    "stop speaking",
    "dont speak",
    "don't speak",
    "be quiet",
    "silent mode",
    "quiet mode",
    "mute speech",
    "mute voice",
    "mute"
]

UNMUTE_PHRASES = [
    "start speaking",
    "speak again",
    "unmute voice",
    "unmute speech",
    "unmute",
    "enable voice",
    "voice on"
]

def check_and_handle_voice_commands(command: str) -> bool:
    """Handles speech mute/unmute and voice switching commands. Returns True if handled."""
    clean = re.sub(r"[^\w\s]", "", command.lower().strip())

    # Check Mute
    for phrase in MUTE_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", clean):
            print("\n[Voice Command]: Stop Speaking (Silent terminal mode)")
            speaker.speak("Got it Omkar, I'll stay quiet and only display text on your terminal.", blocking=True)
            speaker.mute()
            print("[Sky]: 🔇 Speech muted. Future responses will appear as text on terminal only.\n")
            return True

    # Check Unmute
    for phrase in UNMUTE_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", clean):
            print("\n[Voice Command]: Start Speaking (Voice enabled)")
            speaker.unmute()
            print("[Sky]: 🔊 Speech enabled. Sky will speak responses aloud and show them on terminal.\n")
            speaker.speak("Voice output enabled! I will speak with you again.", blocking=True)
            return True

    return False

def is_pc_sleep_phrase(text: str) -> bool:
    """Checks if utterance is an instruction to put the PC/laptop to sleep (system suspend)."""
    clean = re.sub(r"[^\w\s]", "", text.lower().strip())
    # Exclude speech mute/unmute commands
    if any(m in clean for m in ["stop speaking", "start speaking", "mute", "unmute"]):
        return False
    for phrase in PC_SLEEP_PHRASES:
        pattern = rf"\b{re.escape(phrase)}\b"
        if re.search(pattern, clean):
            return True
    return False

def handle_pc_sleep_command():
    """Speaks acknowledgment and puts the laptop/PC hardware to sleep (system suspend)."""
    msg = "Putting your laptop to sleep now. Catch you later, Omkar!"
    print(f"\n[Sky]: {msg}")
    speaker.speak(msg, blocking=True)
    time.sleep(0.5)
    import subprocess
    try:
        subprocess.run(["systemctl", "suspend"], check=False)
    except Exception as e:
        print(f"[Sky]: Could not put PC to sleep: {e}")

def is_stop_phrase(text: str) -> bool:
    """Checks if utterance contains an instruction to terminate the Sky assistant process."""
    clean = re.sub(r"[^\w\s]", "", text.lower().strip())
    
    # Exclude PC sleep commands (PC sleep suspends the laptop, does not terminate Sky)
    if is_pc_sleep_phrase(clean):
        return False

    # Exclude speech mute/unmute commands
    if any(m in clean for m in ["stop speaking", "start speaking", "stop talking", "start talking", "mute", "unmute"]):
        return False

    for phrase in STOP_PHRASES:
        pattern = rf"\b{re.escape(phrase)}\b"
        if re.search(pattern, clean):
            return True
    return False

def handle_stop_command():
    """Bids farewell and shuts down Sky completely."""
    farewell = random.choice(FAREWELL_MESSAGES)
    print(f"\n[Sky]: {farewell}")
    speaker.speak(farewell, blocking=True)
    print("\n[Sky AI] Process terminated. Goodbye Omkar!\n")
    time.sleep(0.3)
    os._exit(0)

def extract_command_from_utterance(text: str) -> Tuple[bool, str]:
    """
    Checks if any wake word is present in the utterance.
    Returns (is_wake_word_detected, stripped_command).
    """
    cleaned = text.lower().strip()
    if not cleaned:
        return False, ""

    # Sort wake words by length descending so "wake up sky" is tested before "sky"
    sorted_keywords = sorted(WAKE_WORDS, key=len, reverse=True)
    
    for kw in sorted_keywords:
        pattern = rf"\b{re.escape(kw)}\b"
        if re.search(pattern, cleaned):
            # Extract the actual task command after the wake phrase
            remainder = re.sub(pattern, "", cleaned, count=1).strip()
            # Clean up leading punctuation or filler words
            remainder = re.sub(r"^(please|could you|can you|,|\.|\s)+", "", remainder).strip()
            return True, remainder

    return False, ""

class WakeWordDetector:
    """
    Hybrid Wake Word Detector supporting both Porcupine and continuous Whisper keyword spotting.
    """

    def __init__(self, on_wake_callback: Callable[[str], None]):
        self.on_wake_callback = on_wake_callback
        self.listener = AudioListener()
        self.is_running = False
        self.porcupine = None

        if PICOVOICE_ACCESS_KEY:
            try:
                import pvporcupine
                self.porcupine = pvporcupine.create(
                    access_key=PICOVOICE_ACCESS_KEY,
                    keywords=["jarvis", "picovoice", "bumblebee"]
                )
            except Exception as e:
                print(f"[WakeWord] Porcupine initialization skipped: {e}")
                self.porcupine = None

    def start_listening(self, verbose: bool = True):
        """Starts the voice listening loop."""
        self.is_running = True
        if verbose:
            print("\n[Sky Voice Engine] Listening for wake phrase ('Hey Sky', 'Wake up Sky', or any sentence with 'Sky')...")
            print("[Tip]: Say 'Call it a day', 'Sky stop', or 'Rest' to shut down Sky, or 'Go to sleep' to sleep PC.\n")

        while self.is_running:
            try:
                # If speaker is actively outputting audio, pause listening to avoid self-triggering
                if getattr(speaker, "is_speaking", False):
                    time.sleep(0.15)
                    continue

                # Capture speech audio
                audio_file = self.listener.record_until_silence(max_seconds=8.0)
                if not audio_file:
                    continue

                if getattr(speaker, "is_speaking", False):
                    continue

                # Transcribe with Whisper
                text = self.listener.transcribe_audio(audio_file)
                if not text:
                    continue

                # Check for PC sleep phrases even before wake word (e.g. "go to sleep")
                if is_pc_sleep_phrase(text):
                    print(f"\n[Voice Command Detected]: \"{text}\" -> PC Sleep Request")
                    handle_pc_sleep_command()
                    continue

                # Check for stop phrases even before wake word (e.g. "call it a day")
                if is_stop_phrase(text):
                    print(f"\n[Voice Command Detected]: \"{text}\" -> Stop Request")
                    self.stop()
                    handle_stop_command()
                    return

                # Check for wake word
                detected, command = extract_command_from_utterance(text)
                if detected:
                    print(f"\n[Wake Word Detected!]: Heard -> \"{text}\"")

                    # Check if command is to sleep PC
                    if is_pc_sleep_phrase(command):
                        print(f"[Command Extracted]: \"{command}\" -> PC Sleep Request")
                        handle_pc_sleep_command()
                        continue

                    # Check if command is to stop Sky
                    if is_stop_phrase(command):
                        print(f"[Command Extracted]: \"{command}\" -> Stop Request")
                        self.stop()
                        handle_stop_command()
                        return

                    # Check if command is mute/unmute
                    if check_and_handle_voice_commands(command):
                        continue

                    if command:
                        print(f"[Command Extracted]: \"{command}\"")
                        self.on_wake_callback(command)
                    else:
                        # User just said "Hey Sky" without a follow-up command
                        speaker.speak("Yes, I am listening.", blocking=True)
                        print("[Sky]: Yes, I'm listening... Please state your command:")
                        # Listen for immediate follow-up
                        followup_file = self.listener.record_until_silence(max_seconds=10.0)
                        if followup_file:
                            followup_cmd = self.listener.transcribe_audio(followup_file)
                            if followup_cmd:
                                if is_pc_sleep_phrase(followup_cmd):
                                    handle_pc_sleep_command()
                                    continue
                                if is_stop_phrase(followup_cmd):
                                    self.stop()
                                    handle_stop_command()
                                    return
                                if check_and_handle_voice_commands(followup_cmd):
                                    continue
                                print(f"[Follow-up Command]: \"{followup_cmd}\"")
                                self.on_wake_callback(followup_cmd)
                            else:
                                speaker.speak("I didn't catch that Omkar. Could you please repeat?", blocking=True)
                        else:
                            speaker.speak("I didn't catch that Omkar. Could you please repeat?", blocking=True)

            except KeyboardInterrupt:
                print("\n[Sky Voice Engine] Stopped listening.")
                break
            except Exception as e:
                print(f"[WakeWord] Listener loop warning: {e}")
                time.sleep(0.5)

    def stop(self):
        self.is_running = False
        if self.porcupine:
            try:
                self.porcupine.delete()
            except Exception:
                pass
