# 🤖 JARVIS Project Status

## 📖 Overview
JARVIS is a full-featured AI desktop assistant built with Tauri (desktop shell), React/TypeScript (frontend), and Python/FastAPI (backend). It features wake word activation, bilingual speech recognition (Bangla & English), voice responses, computer control (PyAutoGUI), browser automation (Playwright), and a dynamic AI brain UI (Three.js/React Three Fiber).

## Current Phase: Phase 2 — Voice (Wake Word + STT + TTS)

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

- [ ] **Phase 2: Voice (Wake Word + STT + TTS, বাংলা+English)**
  - Custom wake word engine (openWakeWord or Picovoice Porcupine)
  - Background mic listener for wake word
  - Speech-to-text via OpenAI gpt-live-transcribe (bilingual: bn + en)
  - Text-to-speech via OpenAI TTS (tts-1, onyx voice)
  - Wake word → Listening state → STT → AI → TTS pipeline

- [ ] Phase 3: AI Brain (Intent Understanding + Planning)
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
  - `tts-1` with `onyx` voice (Text-to-Speech — Phase 2)

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

## 📌 Phase 2 Next Steps (Voice)
1. Install `pyaudio` and `sounddevice` for mic access
2. Install `openwakeword` for wake word detection
3. Implement `backend/voice/wake_word.py` — background mic listener
4. Implement `backend/voice/stt.py` — OpenAI gpt-live-transcribe integration
5. Implement `backend/voice/tts.py` — OpenAI tts-1 + audio playback
6. Wire the pipeline in backend: wake → listen → transcribe → AI → speak
7. Update frontend: WS events from backend trigger brain state changes
8. Wake phrase: user configurable in `.env` as `WAKE_WORD=jarvis`

## ⚠️ Known Issues / TODOs
- Tauri native shell not yet initialized (using browser dev mode)
- `start_backend.bat` assumes Python 3.13 venv path — verify on other machines
