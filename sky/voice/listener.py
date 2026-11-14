import os
import tempfile
import time
import wave
from pathlib import Path
from typing import Optional
import numpy as np
import sounddevice as sd
from groq import Groq

from sky.config import WHISPER_MODEL, get_groq_api_key, rotate_groq_api_key

class AudioListener:
    """Captures microphone audio and transcribes it via Whisper with multi-key fallback."""

    def __init__(
        self,
        sample_rate: int = 16000,
        energy_threshold: float = 0.03,  # Higher threshold to filter out ambient room noise
        silence_limit_seconds: float = 1.2,
    ):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_limit_seconds = silence_limit_seconds
        self._groq_client: Optional[Groq] = None

    @property
    def groq_client(self) -> Groq:
        if self._groq_client is None:
            self._groq_client = Groq(api_key=get_groq_api_key())
        return self._groq_client

    def rotate_client(self):
        new_key = rotate_groq_api_key()
        self._groq_client = Groq(api_key=new_key)

    def record_until_silence(self, max_seconds: float = 15.0) -> Optional[Path]:
        """
        Listens to microphone, begins collecting when sound detected,
        and returns temporary WAV file when silence ensues.
        """
        chunk_duration = 0.1  # 100ms chunks
        chunk_size = int(self.sample_rate * chunk_duration)
        
        frames = []
        is_speaking = False
        silence_start_time = None
        start_time = time.time()

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as stream:
                while time.time() - start_time < max_seconds:
                    chunk, _ = stream.read(chunk_size)
                    rms = np.sqrt(np.mean(chunk**2))

                    if rms > self.energy_threshold:
                        if not is_speaking:
                            is_speaking = True
                        silence_start_time = None
                        frames.append(chunk)
                    elif is_speaking:
                        frames.append(chunk)
                        if silence_start_time is None:
                            silence_start_time = time.time()
                        elif time.time() - silence_start_time >= self.silence_limit_seconds:
                            # Silence reached after speech
                            break
                    else:
                        # Waiting for speech to start
                        time.sleep(0.01)

            # If no speech or speech was too brief (under 0.5 seconds), ignore as noise
            if not frames or len(frames) < 5:
                return None

            # Concatenate chunks and save to WAV
            audio_data = np.concatenate(frames, axis=0)
            # Convert float32 [-1.0, 1.0] to int16
            audio_int16 = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)

            tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = Path(tmp_file.name)
            tmp_file.close()

            with wave.open(str(tmp_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            return tmp_path

        except Exception as e:
            print(f"[Listener] Audio recording error: {e}")
            return None

    def transcribe_audio(self, wav_path: Path) -> str:
        """Sends WAV file to Whisper API and returns text."""
        if not wav_path or not wav_path.exists():
            return ""

        try:
            with open(wav_path, "rb") as f:
                audio_bytes = f.read()
            transcription = self.groq_client.audio.transcriptions.create(
                file=(wav_path.name, audio_bytes),
                model=WHISPER_MODEL,
                response_format="text"
            )
            return str(transcription).strip()
        except Exception as e:
            from sky.config import is_internet_available
            if not is_internet_available() or any(w in str(e).lower() for w in ["connection", "connect", "network"]):
                from sky.voice.speaker import speaker
                print("\n[Sky]: ⚠️ No internet connection detected!")
                speaker.speak_no_internet(blocking=True)
                return ""
            err_str = str(e).lower()
            if "rate limit" in err_str or "429" in err_str or "quota" in err_str:
                try:
                    self.rotate_client()
                    transcription = self.groq_client.audio.transcriptions.create(
                        file=(wav_path.name, audio_bytes),
                        model=WHISPER_MODEL,
                        response_format="text"
                    )
                    return str(transcription).strip()
                except Exception as e2:
                    print(f"[Listener] Whisper fallback transcription error: {e2}")
                    return ""
            else:
                print(f"[Listener] Whisper transcription error: {e}")
                return ""
        finally:
            try:
                wav_path.unlink(missing_ok=True)
            except Exception:
                pass
