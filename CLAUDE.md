# 🤖 JARVIS Project Status

## 📖 Overview
JARVIS is a full-featured AI desktop assistant built with Tauri (desktop shell), React/TypeScript (frontend), and Python/FastAPI (backend). It features wake word activation, bilingual speech recognition (Bangla & English), voice responses, computer control (PyAutoGUI), browser automation (Playwright), and a dynamic AI brain UI (Three.js/React Three Fiber).

## Current Phase: Phase 1: Voice & Basic STT/TTS

## Progress Status
- [x] **Phase 0: Foundation Setup**
  - Project architecture established
  - Python backend configured (FastAPI, WebSockets, dotenv, loguru)
  - Python 3.13 virtual environment set up and verified
  - Vite React frontend initialized (Tailwind v4, Zustand)
  - `start_backend.bat` and `test_phase0.py` validated
- [ ] **Phase 1: Voice & Basic STT/TTS**
  - Implement system audio capture
  - Setup real-time speech-to-text
- [ ] Phase 2: Memory & Context
- [ ] Phase 3: Action Execution
- [ ] Phase 4: UI Polish & System Tray
- ⬜ **Phase 8:** Agentic Multi-Step Tasks
- ⬜ **Phase 9:** Vision (Visual Intelligence)
- ⬜ **Phase 10:** Polish & Safety Hardening

## ⚙️ Current Status
**Currently in:** Phase 1 (Active)

**What was done in Phase 0:**
- Configured `.env` and `.gitignore`.
- Initialized Python backend with FastAPI & WebSocket.
- Set up OpenAI API key validation on backend startup.
- Scaffolded Vite + React + TypeScript + Tailwind frontend.
- Created global Zustand store for connection/brain states and WebSocket manager in the frontend.
- Created `scripts/test_phase0.py` and `scripts/start_backend.bat` for manual verification.

## 📂 Project Structure
```text
jarvis/
├── apps/
│   └── desktop/
│       ├── src/
│       │   ├── components/       # UI components (brain, panels, cards)
│       │   ├── features/         # voice, memory, conversation features
│       │   ├── stores/           # zustand state
│       │   └── lib/              # WebSocket manager
│       └── src-tauri/            # Tauri 2 configuration
├── backend/
│   ├── api/                      # FastAPI routes + websocket (main.py)
│   ├── core/                     # config, settings, env (config.py)
│   ├── ai/                       # LLM routing
│   ├── voice/                    # wake word, STT, TTS
│   ├── memory/                   # SQLite models
│   ├── planner/                  # intent → tool-call planning
│   ├── vision/                   # screen understanding
│   └── tools/                    # PyAutoGUI, Playwright, system controls
├── shared/                       # shared types/schemas
├── scripts/                      # test & startup scripts
├── tests/
├── .env
└── CLAUDE.md
```

## 🛠️ Tech Stack & Models
- **Desktop Shell:** Tauri 2
- **Frontend:** React + TypeScript + Vite + Tailwind CSS + Framer Motion + Zustand
- **Backend:** Python 3 + FastAPI + WebSocket + Loguru
- **Models Used:**
  - `gpt-5.6-luna` (Default Reasoning)
  - `gpt-5.6-terra` (Complex Reasoning)
  - `gpt-live-transcribe` (Speech-to-Text)
  - `tts-1` with `onyx` voice (Text-to-Speech)

## 📌 Next Steps (For Next Session)
1. **User verification:** The user needs to run `scripts\start_backend.bat`, followed by `backend\.venv\Scripts\python.exe scripts\test_phase0.py` to confirm the backend is solid. Then start the frontend using `cd apps\desktop` and `npm run dev`.
2. **Phase 1 (Jarvis UI):** After Phase 0 is verified, move to Phase 1. Build the central "AI Brain" visual using Three.js/React Three Fiber with animated states (Idle / Listening / Thinking / Executing / Speaking). Implement System status panel, Conversation panel, and Active Memory panel using Tailwind CSS and Framer Motion. Connect the dummy states to the Zustand store.

## ⚠️ Known Issues / TODOs
- Tauri CLI initialization requires correct MSVC build tools setup. The frontend currently operates as a standard Vite React app communicating with the backend over WebSocket. Tauri native initialization will be fully wrapped in subsequent phases as needed.
