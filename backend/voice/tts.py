import httpx
from loguru import logger
from backend.core.config import settings

class TextToSpeechEngine:
    def __init__(self, api_key: str = "", voice: str = ""):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id
        
        if not self.api_key or "your_elevenlabs_key" in self.api_key:
            logger.warning("ElevenLabs API Key is missing or invalid.")

    async def generate_speech(self, text: str) -> bytes:
        """
        Takes text and returns MP3 audio bytes using ElevenLabs TTS via REST API.
        """
        logger.info(f"Generating speech (ElevenLabs, voice_id={self.voice_id})...")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_v3",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"ElevenLabs API Error: {response.status_code} - {response.text}")
                    return b""
                
                audio_bytes = response.content
                logger.success(f"Generated {len(audio_bytes)} bytes of audio.")
                return audio_bytes

        except Exception as e:
            logger.error(f"Error generating speech from ElevenLabs: {e}")
            return b""
