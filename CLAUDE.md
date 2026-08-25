# 🤖 JARVIS Project Status

## 📖 Overview

JARVIS is a full-featured AI desktop assistant built with Tauri (desktop shell), React/TypeScript (frontend), and Python/FastAPI (backend). It features wake word activation, bilingual speech recognition (Bangla & English), voice responses, computer control (PyAutoGUI), browser automation (Playwright), and a dynamic AI brain UI (Three.js/React Three Fiber).

## Current Phase: Phase 3 — AI Brain (Intent Understanding + Planning)

## Progress Status

- [x] **Phase 0: Foundation Setup** ✅
  - Python 3.13 virtual environment (26 packages installed)
  - FastAPI + WebSocket backend running on port 8765
  - Vite + React + TypeScript + Tailwind frontend
  - OpenAI API key validation on startup
  - test_phase0.py: ALL PASS

- [x] **Phase 1: Jarvis UI** ✅
  - 3D animated brain orb (Three.js / React Three Fiber)
  - 5 animated brain states: Idle / Listening / Thinking / Executing / Speaking
  - System Status Panel (CPU, RAM, Network, Uptime — live-simulated)
  - Conversation Panel (User/Jarvis message bubbles, auto-scroll)
  - Active Memory Panel (categorized memory entries)
  - Status Bar (brain state badge, connection indicator)
  - Dev Controls (manual state trigger buttons)
  - Global design system (glass panels, glow effects, scan lines, grid bg)
  - test_phase1.py: ALL PASS

- [x] **Phase 2: Voice (Wake Word + STT + TTS, বাংলা+English)** ✅
  - Custom wake word engine (`openWakeWord` forced to `onnxruntime` due to Windows/Py3.13 tflite issues)
  - Background mic listener for "Hey Jarvis" (`backend/voice/wake_word.py`) — threshold tuned to 0.25 for Bangladeshi accent
  - Speech-to-text via OpenAI `gpt-4o-transcribe` (better Bengali accuracy than Whisper) (`backend/voice/stt.py`)
  - Text-to-speech via ElevenLabs Premium TTS (Voice: Charlie) (`backend/voice/tts.py`)
  - Audio playback using `pyaudio` and `miniaudio` (pure Python MP3 decode without ffmpeg) (`backend/voice/audio_player.py`)
  - Wake word → Listening state → STT → TTS pipeline running seamlessly in `backend/api/main.py`
  - Voice pipeline syncs perfectly with React UI states (`Listening`, `Thinking`, `Speaking`) via WebSocket.
  - **Modification**: As per user request, Phase 2 bypasses AI reasoning and translation, directly echoing STT transcripts to TTS.

- [x] **Phase 3: AI Brain (Intent Understanding + Planning)** ✅
  - Integrated `AIBrain` for intent routing (Luna default, Terra fallback).
  - Defined tool schemas (`open_app`, `close_app`, `set_volume`, `search_file`).
  - Added SQLite-backed `RateLimitGuard` (500 limit).
- [ ] Phase 4: Basic Computer Control
- [ ] Phase 5: File System Control
- [ ] Phase 6: Browser Automation
- [ ] Phase 7: Memory
- [ ] Phase 8: Agentic Multi-Step Tasks
- [ ] Phase 9: Vision
- [ ] Phase 10: Polish & Safety Hardening

## 📂 Project Structure

```text
jarvis/
├── apps/
│   └── desktop/
│       ├── src/
│       │   ├── components/
│       │   │   ├── JarvisBrain.tsx         ← 3D animated brain (Three.js)
│       │   │   ├── CenterBrainSection.tsx  ← Brain + rotating rings
│       │   │   ├── ConversationPanel.tsx   ← Chat UI
│       │   │   ├── SystemStatusPanel.tsx   ← CPU/RAM/Network
│       │   │   ├── ActiveMemoryPanel.tsx   ← Memory entries
│       │   │   ├── StatusBar.tsx           ← Top header
│       │   │   └── BrainStateControls.tsx  ← Dev controls
│       │   ├── stores/
│       │   │   └── jarvisStore.ts          ← Zustand global state
│       │   ├── lib/
│       │   │   └── websocket.ts            ← WS manager
│       │   ├── App.tsx                     ← 3-column layout
│       │   └── index.css                   ← Full design system
│       └── package.json
├── backend/
│   ├── api/main.py                         ← FastAPI + WebSocket
│   ├── core/config.py                      ← Settings (pydantic)
│   ├── voice/                              ← Phase 2: STT/TTS/wake word
│   └── requirements.txt
├── scripts/
│   ├── test_phase0.py                      ← Phase 0 sanity check
│   ├── test_phase1.py                      ← Phase 1 sanity check
│   └── start_backend.bat
└── .env
```

## 🛠️ Tech Stack & Models

- **Desktop Shell:** Tauri 2 (future)
- **Frontend:** React 19 + TypeScript + Vite + Tailwind CSS v4 + Framer Motion + Three.js (React Three Fiber) + Zustand
- **Backend:** Python 3.13 + FastAPI + WebSocket + Loguru
- **3D:** @react-three/fiber + @react-three/drei + three.js
- **Models Used:**
  - `gpt-5.6-luna` (Default Reasoning)
  - `gpt-5.6-terra` (Complex Reasoning)
  - `gpt-live-transcribe` (Speech-to-Text — Phase 2)
  - `eleven_multilingual_v2` with `Charlie` voice (Text-to-Speech — Phase 2)

## 🚀 Running the App (Development)

```bash
# Terminal 1: Backend
scripts\start_backend.bat

# Terminal 2: Frontend
cd apps\desktop
npm run dev

# Browser
open http://localhost:5173
```

## 🧪 Test Commands

```bash
# Phase 0 test
$env:PYTHONIOENCODING="utf-8"; backend\.venv\Scripts\python.exe scripts\test_phase0.py

# Phase 1 test (backend must be running + npm run dev)
$env:PYTHONIOENCODING="utf-8"; backend\.venv\Scripts\python.exe scripts\test_phase1.py
```

## 📌 Phase 4 Next Steps (Basic Computer Control)

1. Implement PyAutoGUI actions in `backend/tools/system/` and `backend/tools/apps/`.
2. Connect `AIBrain` intent tool calls to actual function executions.
3. Handle Windows-specific requirements like `pycaw` for volume and `screen-brightness-control` for brightness.
4. Provide TTS feedback upon successful completion of computer commands.

## ⚠️ Known Issues / TODOs

- Tauri native shell not yet initialized (using browser dev mode)
- `start_backend.bat` assumes Python 3.13 venv path — verify on other machines
