import io
import asyncio
import pyaudio
import miniaudio
from loguru import logger


class AudioPlayer:
    """
    Plays audio from edge-tts (MP3) or raw PCM bytes.
    Uses miniaudio for MP3 decode — no ffmpeg required.
    """

    def __init__(self):
        self.pyaudio = pyaudio.PyAudio()

    async def play_audio_async(self, audio_data: bytes):
        """Play MP3 or PCM audio bytes asynchronously (non-blocking)."""
        if not audio_data:
            return
        logger.info("Playing audio...")
        await asyncio.to_thread(self._play, audio_data)
        # Wait for the OS audio buffer AND room acoustics to settle before
        # the STT microphone turns on. 1.2s covers both buffer drain + reverb.
        await asyncio.sleep(1.2)

    def _play(self, audio_data: bytes):
        """Detect format and play accordingly."""
        # MP3 magic bytes: ID3 tag or MPEG sync word
        is_mp3 = (
            audio_data[:3] == b"ID3"
            or (len(audio_data) >= 2 and audio_data[0] == 0xFF and (audio_data[1] & 0xE0) == 0xE0)
        )
        if is_mp3:
            self._play_mp3(audio_data)
        else:
            self._play_pcm(audio_data)

    def _play_mp3(self, mp3_data: bytes):
        """Decode MP3 with miniaudio (no ffmpeg needed) and play via pyaudio."""
        stream = None
        try:
            # Force 16-bit signed output so format is always known
            decoded = miniaudio.decode(
                mp3_data,
                output_format=miniaudio.SampleFormat.SIGNED16
            )
            pcm = bytes(decoded.samples)
            stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=decoded.nchannels,
                rate=decoded.sample_rate,
                output=True
            )
            stream.write(pcm)
            logger.success("Audio playback complete.")
        except Exception as e:
            logger.error(f"MP3 playback error: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()

    def _play_pcm(self, pcm_data: bytes):
        """Play raw PCM (24kHz, 16-bit, mono) — legacy fallback."""
        stream = None
        try:
            stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=24000,
                output=True
            )
            stream.write(pcm_data)
        except Exception as e:
            logger.error(f"PCM playback error: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()

    def cleanup(self):
        self.pyaudio.terminate()
