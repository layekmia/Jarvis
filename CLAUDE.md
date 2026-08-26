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
  - **Update**: STT language lock (`language="bn"`) removed — now handles Bangladeshi accent, Bangla, Banglish, and mixed-language input via prompt-guided `gpt-4o-transcribe`.
  - **Update**: Cinematic wake greeting added — when "Hey Jarvis" is detected, Jarvis instantly says _"Yes, sir. I'm online and ready. How can I assist you today?"_ before listening.

- [x] **Phase 3: AI Brain (Intent Understanding + Planning)** ✅
  - Integrated `AIBrain` for intent routing (Luna default, Terra fallback).
  - Defined tool schemas (`open_app`, `close_app`, `set_volume`, `search_file`).
  - Added SQLite-backed `RateLimitGuard` (500 limit).
  - **Update**: Jarvis always responds in English regardless of input language (English, Bangla, Banglish, or mixed). System prompt enforces English-only output.
  - **Update**: Active listening loop added. After waking up, Jarvis stays awake and keeps listening for consecutive commands until the user says "sleep" or "goodbye" or stays silent.
  - **Update**: STT `pause_threshold` increased to 2.5s to prevent cutting off the user mid-sentence if they pause while speaking.
- [x] **Phase 4: Basic Computer Control** ✅
  - Installed Windows dependencies: `pyautogui`, `pycaw`, `screen-brightness-control`, `psutil`, `pygetwindow`, `comtypes`.
  - Created `backend/tools/system.py` (volume, brightness, system info).
  - Created `backend/tools/apps.py` (open, close, switch apps on Windows).
  - Created `backend/tools/interaction.py` (type text, click, screenshot).
  - Added **Tool Dispatcher & Real-Time Narration** in `backend/ai/planner.py`. Jarvis now narrates step-by-step actions (e.g., "Opening notepad...", "Done, sir") while executing tools.
  - Handled silent/soft notifications for actions like closing apps ("বন্ধ করছি...").
- [x] **Phase 5: File System Control** ✅
  - Created `backend/tools/files/file_tools.py` with full file system tools.
  - Tools: `search_file`, `create_file`, `read_file_summary`, `copy_file`, `move_file`, `rename_file`, `delete_file`, `list_directory`.
  - Destructive operations (`move`, `rename`, `delete`) return a `CONFIRM_NEEDED:` sentinel — the AI brain intercepts this and waits for the user to say yes/no before executing.
  - Safety guard: all operations are restricted to `ALLOWED_ROOTS` (home dir and sub-dirs). Attempts to access system paths (e.g. `C:\Windows`) are blocked.
  - `AIBrain` in `planner.py` updated with `_pending_confirmation` state and `_handle_pending_confirmation()` to resolve yes/no voice replies.
  - `backend/planner/schema.py` updated with Phase 5 tool schemas.
  - `scripts/test_phase5.py`: **22/22 tests PASS**.
- [x] **Phase 6: Browser Automation** ✅
  - Installed Playwright and Chromium.
  - Created `backend/tools/browser/browser_tools.py` using Playwright's sync API.
  - Features: `open_url`, `search_web`, `youtube_search`, `fill_form`, `switch_tab`, `close_browser`.
  - Maintains a singleton Playwright browser instance so consecutive tool calls operate on the same window.
  - Handled generic selectors and Google/YouTube consent flows dynamically.
  - Added tools to `schema.py` and `planner.py`.
- [x] **Phase 7: Memory** ✅
  - Created SQLite memory database (`backend/memory/db.py`) with UPSERT logic (unique `category` + `label`).
  - Added AI memory tools: `remember` and `forget`.
  - Updated LLM `SYSTEM_PROMPT` to spontaneously remember user facts/preferences.
  - Implemented Short-term Conversation Buffer: AI Brain now keeps the last 16 messages (8 turns) in session memory to maintain conversational continuity.
  - Injected explicit memory (from DB) into the `SYSTEM_PROMPT` dynamically on every turn.
  - Built WebSocket event `set_memory` to sync real-time active memories to the frontend `ActiveMemoryPanel.tsx`.
  - Frontend Zustand store updated to reactively display synced memories without dummy data.
  - `scripts/test_phase7.py`: **ALL PASS**.
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

## 📌 Phase 8 Next Steps (Agentic Multi-Step Tasks)

1. Build a multi-step task planner inside `backend/ai/`.
2. Break down complex commands (e.g. "set up my dev environment") into a list of sequential steps.
3. Execute each step sequentially, handling failures and retries.
4. Add a progress tracker UI in the frontend and stream progress via WebSocket.
5. Update `CLAUDE.md` and git commit.

## ⚠️ Known Issues / TODOs

- Tauri native shell not yet initialized (using browser dev mode)
- `start_backend.bat` assumes Python 3.13 venv path — verify on other machines
