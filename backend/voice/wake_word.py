import asyncio
import os
import pyaudio
import numpy as np
from loguru import logger
import openwakeword
from openwakeword.model import Model

# Optional: Download models if they don't exist. openwakeword usually handles this or comes with pre-trained models.
# The default model "hey_jarvis" is available in openwakeword.

class WakeWordEngine:
    def __init__(self, wake_word="hey_jarvis", threshold=0.25):
        self.wake_word = wake_word
        self.threshold = threshold
        self.is_listening = False
        
        # Audio settings for openwakeword (16kHz, 16-bit, mono)
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1280
        
        self.audio = None
        self.mic_stream = None
        
        logger.info(f"Initializing Wake Word engine for '{self.wake_word}'...")
        try:
            # Download ONNX models if not already present (runs once)
            openwakeword.utils.download_models()
            # Force onnxruntime — tflite-runtime is not available on Python 3.13/Windows
            self.model = Model(wakeword_models=[self.wake_word], inference_framework="onnx")
            logger.info("✅ Wake Word engine initialized successfully (onnxruntime).")
        except Exception as e:
            logger.error(f"Failed to initialize openwakeword: {e}")
            self.model = None

    def start_mic(self):
        if self.audio is None:
            self.audio = pyaudio.PyAudio()
        
        if self.mic_stream is None:
            self.mic_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
        logger.info("Microphone started for wake word detection.")

    def stop_mic(self):
        if self.mic_stream is not None:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
            self.mic_stream = None
        if self.audio is not None:
            self.audio.terminate()
            self.audio = None
        logger.info("Microphone stopped.")

    async def listen_for_wake_word(self) -> bool:
        """
        Listens continuously until the wake word is detected.
        Returns True when detected.
        """
        if self.model is None:
            raise RuntimeError("Wake word model is not initialized. Cannot listen.")

        self.is_listening = True
        self.start_mic()
        
        logger.info(f"Listening for wake word: '{self.wake_word}'...")
        
        try:
            while self.is_listening:
                # Read audio chunk
                pcm = self.mic_stream.read(self.CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(pcm, dtype=np.int16)
                
                # Predict wake word
                prediction = self.model.predict(audio_data)
                
                # Check threshold
                for model_name, score in prediction.items():
                    if score > self.threshold:
                        logger.success(f"Wake word '{model_name}' detected! Score: {score:.2f}")
                        self.is_listening = False
                        self.stop_mic()
                        return True
                        
                # Yield control to the event loop so this doesn't block the thread completely
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error during wake word detection: {e}")
        finally:
            self.stop_mic()
            
        return False
