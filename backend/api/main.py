"""
Jarvis FastAPI Backend — WebSocket server with ping-pong test endpoint.

Startup checklist:
  1. Loads config (fails loud if OPENAI_API_KEY missing)
  2. Validates OpenAI key with a /models call
  3. Exposes WebSocket at ws://127.0.0.1:8765/ws
  4. Sends 'connected' event to frontend on WebSocket connect
"""

import json
import asyncio
from datetime import datetime
from typing import Any

# pyrefly: ignore [missing-import]
import httpx
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from loguru import logger

from backend.core.config import settings
from backend.voice.wake_word import WakeWordEngine
from backend.voice.stt import SpeechToTextEngine
from backend.voice.tts import TextToSpeechEngine
from backend.voice.audio_player import AudioPlayer
from backend.memory.guard import RateLimitGuard, RateLimitExceeded
from backend.memory.db import init_db, get_all_memories
from backend.ai.planner import AIBrain

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Jarvis Backend",
    description="AI Desktop Assistant Backend",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tauri webview origin — tightened in later phases
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track connected WebSocket clients
connected_clients: list[WebSocket] = []


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event() -> None:
    """Runs on server start. Validates OpenAI API key."""
    logger.info("🚀 Jarvis backend starting...")
    init_db()
    await validate_openai_key()
    
    # Start voice engine loop in the background
    asyncio.create_task(voice_loop())
    
    logger.info("✅ Jarvis backend ready!")


async def validate_openai_key() -> None:
    """
    Calls OpenAI /models endpoint to verify the API key works.
    Exits with a clear error message if it fails — never silently continues.
    """
    logger.info("🔑 Validating OpenAI API key...")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{settings.openai_base_url}/models",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"}
            )
            if response.status_code == 200:
                logger.info("✅ OpenAI API key validated successfully!")
            elif response.status_code == 401:
                logger.critical(
                    "❌ FATAL: OpenAI API key is INVALID (401 Unauthorized)!\n"
                    "   Update OPENAI_API_KEY in your .env file and restart."
                )
                raise SystemExit(1)
            else:
                logger.warning(
                    f"⚠️  OpenAI /models returned HTTP {response.status_code}. "
                    f"Continuing anyway — may be a transient issue."
                )
    except httpx.ConnectError:
        logger.warning(
            "⚠️  Could not reach OpenAI API (no internet?). "
            "Jarvis will start, but AI features won't work without internet."
        )
    except SystemExit:
        raise
    except Exception as e:
        logger.warning(f"⚠️  OpenAI key validation failed with unexpected error: {e}")


# ── HTTP routes ───────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "service": "jarvis-backend",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "model_default": settings.model_reasoning_default,
        "model_complex": settings.model_reasoning_complex,
        "clients_connected": len(connected_clients),
    }


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Jarvis Backend is running. Connect via WebSocket at /ws"}


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Main WebSocket endpoint.
    - Sends 'connected' event immediately on connect.
    - Handles ping → pong for Phase 0 testing.
    - Gracefully handles disconnect.
    """
    await websocket.accept()
    connected_clients.append(websocket)
    client_id = id(websocket)
    logger.info(f"🔌 WebSocket client connected (id={client_id}). Total: {len(connected_clients)}")

    # Send initial connection confirmation
    await send_event(websocket, "connected", {
        "message": "Jarvis backend connected!",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Send initial memory state
    await send_event(websocket, "set_memory", {
        "entries": get_all_memories()
    })

    try:
        while True:
            raw = await websocket.receive_text()
            logger.debug(f"📨 Received from {client_id}: {raw}")

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await send_event(websocket, "error", {"message": f"Invalid JSON: {raw}"})
                continue

            event_type = data.get("type", "")
            payload = data.get("payload", {})

            await handle_event(websocket, event_type, payload)

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket client disconnected (id={client_id})")
    except Exception as e:
        logger.error(f"❌ WebSocket error for client {client_id}: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        logger.info(f"   Remaining clients: {len(connected_clients)}")


async def handle_event(
    websocket: WebSocket,
    event_type: str,
    payload: dict[str, Any]
) -> None:
    """Route incoming WebSocket events to the appropriate handler."""

    if event_type == "ping":
        # Phase 0 ping-pong test
        await send_event(websocket, "pong", {
            "message": "pong!",
            "timestamp": datetime.utcnow().isoformat(),
            "echo": payload.get("message", ""),
        })

    elif event_type == "status":
        # Return backend status
        await send_event(websocket, "status_response", {
            "backend_running": True,
            "version": "0.1.0",
            "models": {
                "default": settings.model_reasoning_default,
                "complex": settings.model_reasoning_complex,
            },
            "clients_connected": len(connected_clients),
        })

    else:
        logger.warning(f"⚠️  Unknown event type: '{event_type}'")
        await send_event(websocket, "error", {
            "message": f"Unknown event type: '{event_type}'",
            "received_payload": payload,
        })


async def send_event(
    websocket: WebSocket,
    event_type: str,
    payload: dict[str, Any]
) -> None:
    """Helper: send a structured JSON event over WebSocket."""
    message = json.dumps({
        "type": event_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat(),
    })
    await websocket.send_text(message)
    logger.debug(f"📤 Sent event '{event_type}'")


async def broadcast_event(event_type: str, payload: dict[str, Any]) -> None:
    """Broadcasts an event to all connected WebSocket clients."""
    if not connected_clients:
        return
    message = json.dumps({
        "type": event_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat(),
    })
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            pass


async def voice_loop() -> None:
    """Background loop that handles wake word detection and voice interaction."""
    logger.info("Starting background voice loop...")
    
    # Initialize engines
    wake_engine = WakeWordEngine(wake_word="hey_jarvis")
    stt_engine = SpeechToTextEngine(api_key=settings.openai_api_key)
    tts_engine = TextToSpeechEngine(api_key=settings.openai_api_key)
    player = AudioPlayer()
    brain = AIBrain()
    guard = RateLimitGuard(daily_limit=settings.daily_request_limit)
    
    while True:
        try:
            # 1. Listen for wake word
            await broadcast_event("brain_state", {"state": "idle"})
            detected = await wake_engine.listen_for_wake_word()
            
            if not detected:
                continue
                
            # Wake word detected! Update UI
            logger.info("Wake word detected. Switching UI to Listening...")
            
            # 2a. Play cinematic wake greeting (Speaking state briefly)
            await broadcast_event("brain_state", {"state": "speaking"})
            greeting = "Yes, sir. I'm online and ready. How can I assist you today?"
            greeting_audio = await tts_engine.generate_speech(greeting)
            await player.play_audio_async(greeting_audio)
            logger.info(f"Played wake greeting: '{greeting}'")
            
            # Active listening loop: Keep listening until user explicitly says to stop.
            # Timeouts / empty transcriptions do NOT exit this loop —
            # only explicit sleep commands from the user will break it.
            consecutive_timeouts: int = 0
            MAX_CONSECUTIVE_TIMEOUTS: int = 10  # safety valve: ~10 × 10s = ~100s of total silence

            while True:
                # Switch UI to Listening
                await broadcast_event("brain_state", {"state": "listening"})

                # Record and transcribe
                text = await stt_engine.listen_and_transcribe()

                if not text:
                    consecutive_timeouts += 1
                    logger.info(
                        f"No speech detected (timeout #{consecutive_timeouts}/{MAX_CONSECUTIVE_TIMEOUTS}). "
                        "Staying in listening mode — waiting for your command..."
                    )
                    # Only go to sleep after MAX_CONSECUTIVE_TIMEOUTS of pure silence
                    if consecutive_timeouts >= MAX_CONSECUTIVE_TIMEOUTS:
                        logger.info(
                            f"Reached {MAX_CONSECUTIVE_TIMEOUTS} consecutive timeouts. "
                            "Going to sleep (safety timeout)."
                        )
                        await broadcast_event("brain_state", {"state": "idle"})
                        break
                    # Otherwise keep looping — don't sleep
                    continue

                # Got speech — reset timeout counter
                consecutive_timeouts = 0

                # Check for explicit sleep commands
                text_lower = text.lower()
                sleep_phrases = [
                    "sleep", "stop listening", "goodbye", "bye",
                    "go to sleep", "ঘুমাও", "ঘুমিয়ে যাও", "বিশ্রাম নাও"
                ]
                if any(phrase in text_lower for phrase in sleep_phrases):
                    logger.info("Sleep command received. Going back to sleep mode.")
                    await broadcast_event("brain_state", {"state": "idle"})
                    break

                # Send transcribed text to UI
                await broadcast_event("message", {"text": text, "role": "user"})

                # 3. AI Brain
                await broadcast_event("brain_state", {"state": "thinking"})

                try:
                    guard.check_limit()
                    response_text = await brain.process_intent(
                        text,
                        tts_engine=tts_engine,
                        player=player,
                        broadcast_callback=broadcast_event
                    )
                    guard.log_usage(tokens=1)
                except RateLimitExceeded:
                    response_text = "I've reached my daily usage limit. Please try again tomorrow."
                except Exception as brain_err:
                    logger.error(f"Brain processing failed: {brain_err}")
                    response_text = "I'm having trouble reaching my AI server right now. Please try again shortly."

                # 4. TTS + Play
                await broadcast_event("brain_state", {"state": "speaking"})
                await broadcast_event("message", {"text": response_text, "role": "jarvis"})

                audio_bytes = await tts_engine.generate_speech(response_text)
                await player.play_audio_async(audio_bytes)

                # Sync memory to all connected clients in case AI used remember/forget
                await broadcast_event("set_memory", {"entries": get_all_memories()})

                # Loop continues — back to listening state automatically

        except Exception as e:
            logger.error(f"Error in voice loop: {e}")
            await asyncio.sleep(2)



# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
