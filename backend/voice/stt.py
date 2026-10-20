import speech_recognition as sr
from loguru import logger
from openai import AsyncOpenAI
import io
import asyncio


class SpeechToTextEngine:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.recognizer = sr.Recognizer()

        # ── Tuned for fast response ───────────────────────────────────────────
        # energy_threshold: 400 avoids picking up TTS room echo
        self.recognizer.energy_threshold = 400
        # dynamic_energy_threshold adjusts automatically to ambient noise
        self.recognizer.dynamic_energy_threshold = True
        # pause_threshold: how long silence must last before speech is considered done.
        # 1.2s = snappy cutoff while still allowing natural mid-sentence pauses.
        # (Previously 1.8s — that 0.6s difference is very noticeable over many turns)
        self.recognizer.pause_threshold = 1.2
        # non_speaking_duration: trim leading/trailing silence from the audio clip
        self.recognizer.non_speaking_duration = 0.3

        # ── One-time ambient noise calibration at startup ─────────────────────
        # This used to happen on EVERY listen cycle (0.5s wasted each time + the
        # first words of the command were sometimes clipped). Now it runs once.
        self._calibrated = False
        self._calibrate_once()

    def _calibrate_once(self) -> None:
        """Calibrate ambient noise once at startup so _record_audio is instant."""
        try:
            with sr.Microphone() as source:
                logger.info("🎙️  Calibrating ambient noise (one-time)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                self._calibrated = True
                logger.success("✅ Ambient noise calibrated.")
        except Exception as e:
            logger.warning(f"⚠️  Ambient noise calibration failed (non-fatal): {e}")

    async def listen_and_transcribe(self) -> str:
        """
        Listens to the microphone until silence is detected,
        then sends the audio to OpenAI for transcription.

        Speed optimisations applied:
        - No per-cycle noise calibration (done once at __init__)
        - pause_threshold lowered to 1.2s (was 1.8s)
        - gpt-transcribe: correct REST-compatible model for file transcription
          (gpt-live-transcribe is WebSocket-only — cannot be used here)
        - phrase_time_limit kept at 20s to allow long commands
        """
        try:
            # Run synchronous PyAudio recording in a thread (non-blocking)
            audio_data = await asyncio.to_thread(self._record_audio)

            if audio_data is None:
                return ""

            logger.info("🎤 Audio recorded. Transcribing...")

            # Convert to WAV bytes for the API
            wav_data = audio_data.get_wav_data()
            audio_file = io.BytesIO(wav_data)
            audio_file.name = "audio.wav"

            # ── OpenAI Transcription API ──────────────────────────────────────
            # Using gpt-transcribe (2026 recommended batch/file model).
            # - Handles Bangladeshi English accent, Bangla, Banglish, mixed.
            # - gpt-live-transcribe is WebSocket Realtime only — NOT usable here.
            response = await self.client.audio.transcriptions.create(
                model="gpt-transcribe",
                file=audio_file,
                prompt=(
                    "The speaker is Bangladeshi and may speak in English with a Bangladeshi accent, "
                    "in Bengali (Bangla), in Banglish (Bengali words written in English letters), "
                    "or a mix of all of these. Transcribe exactly what is said, preserving the "
                    "original words and language as spoken."
                ),
            )

            transcription = response.text.strip()
            logger.success(f"📝 Transcription: {transcription}")
            return transcription

        except Exception as e:
            logger.error(f"❌ Error during Speech-to-Text: {e}")
            return ""

    def _record_audio(self) -> sr.AudioData:
        """
        Synchronous audio recording. No noise calibration here —
        calibration happens once at __init__ for instant response.
        """
        with sr.Microphone() as source:
            logger.info("👂 Listening for command...")
            try:
                # timeout=15  : wait up to 15s for speech to START
                # phrase_time_limit=20 : max 20s utterance length
                audio = self.recognizer.listen(source, timeout=15, phrase_time_limit=20)
                return audio
            except sr.WaitTimeoutError:
                logger.warning("⏱️  Listening timed out. No speech detected.")
                return None
            except Exception as e:
                logger.error(f"🎙️  Microphone recording error: {e}")
                return None
