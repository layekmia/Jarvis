import speech_recognition as sr
from loguru import logger
from openai import AsyncOpenAI
import io
import asyncio

class SpeechToTextEngine:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.recognizer = sr.Recognizer()
        
        # Adjust these values based on environment noise
        self.recognizer.energy_threshold = 300  
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.2  # Seconds of silence before assuming phrase is done
        
    async def listen_and_transcribe(self) -> str:
        """
        Listens to the microphone until silence is detected, 
        then sends the audio to OpenAI Whisper for transcription.
        """
        try:
            # We run the synchronous PyAudio recording in a separate thread so it doesn't block asyncio
            audio_data = await asyncio.to_thread(self._record_audio)
            
            if audio_data is None:
                return ""
                
            logger.info("Audio recorded. Transcribing via Whisper...")
            
            # Convert audio data to WAV format bytes
            wav_data = audio_data.get_wav_data()
            
            # Create a file-like object for the OpenAI client
            audio_file = io.BytesIO(wav_data)
            audio_file.name = "audio.wav"
            
            # Call OpenAI Transcription API
            # gpt-4o-transcribe has much better Bengali accuracy than whisper-1
            response = await self.client.audio.transcriptions.create(
                model="gpt-4o-transcribe", 
                file=audio_file,
                language="bn",  # Bengali — supported by gpt-4o-transcribe
                prompt="The speaker is talking in Bengali (Bangla). Transcribe accurately in Bengali script.",
            )
            
            transcription = response.text.strip()
            logger.success(f"Transcription: {transcription}")
            return transcription
            
        except Exception as e:
            logger.error(f"Error during Speech-to-Text: {e}")
            return ""

    def _record_audio(self) -> sr.AudioData:
        """Synchronous audio recording with SpeechRecognition."""
        with sr.Microphone() as source:
            logger.info("Calibrating ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            logger.info("Listening for command...")
            try:
                # timeout: wait maximum X seconds for speech to start
                # phrase_time_limit: maximum length of phrase
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                return audio
            except sr.WaitTimeoutError:
                logger.warning("Listening timed out. No speech detected.")
                return None
            except Exception as e:
                logger.error(f"Microphone recording error: {e}")
                return None
