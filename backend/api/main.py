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

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.core.config import settings

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
    await validate_openai_key()
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


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
