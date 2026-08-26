# 🚀 Jarvis

**Jarvis** is an advanced, AI-powered voice assistant for Windows. It features wake word detection, native Bangla/Banglish voice input support, high-quality TTS, multi-step task planning, and deep system integration for controlling apps, files, browsers, and more. 

Built with a robust **FastAPI** backend and a sleek **Tauri + React** frontend desktop application.

---

## ✨ Key Features

### 🎙️ Voice & AI Intelligence
* **Wake Word Detection:** Always listening for `"hey_jarvis"` using OpenWakeWord.
* **Smart STT:** Uses `gpt-4o-transcribe` to understand English, Bengali (Bangla), and Banglish seamlessly.
* **Premium TTS:** Cinematic voice output via ElevenLabs (with Edge-TTS fallback).
* **AI Brain:** Powered by custom Luna/Terra models with a multi-step `AgenticPlanner` for complex reasoning.

### 💻 Computer Control (Phase 4)
* **Smart App Launcher:** Open, close, or switch apps with fuzzy name matching (`rapidfuzz`).
* **Chrome Profile-Aware Launcher:** Launches Chrome or Edge using specific user profiles, bypassing the annoying profile picker.
* **System Controls:** Adjust volume, set screen brightness, and get system information.
* **Safe Power Management:** Shutdown or restart the PC with mandatory user confirmation flows.

### 📁 File System Automation (Phase 5)
* **Fuzzy File Search:** Quickly find files and directories even if you don't remember the exact name.
* **File Operations:** Create, read, move, copy, rename, and delete files (dangerous actions require confirmation).

### 🌐 Browser Automation (Phase 6)
* **Playwright Integration:** Seamlessly open URLs, search the web, fill forms, and switch tabs.
* **YouTube Supercharged:** 
  * `youtube_play`: Uses `yt-dlp` to extract direct video URLs and play them instantly in a specific Chrome profile.
  * Profile-aware YouTube searching and homepage launching.

### 🧠 Long-Term Memory (Phase 7)
* **SQLite-Backed:** Automatically remembers important facts, user preferences, and context (`remember` / `forget` tools).
* **Rate Limit Guard:** Built-in safeguards for API usage.

### 👁️ Vision Capabilities (Phase 9)
* **Screen Context:** Can take screenshots, describe what's on the screen (`describe_screen`), and intelligently interact with UI elements (`click_element_on_screen`).

---

## 🛠️ Technology Stack

* **Backend:** Python, FastAPI, asyncio, Playwright, SQLite, yt-dlp, rapidfuzz, SpeechRecognition, PyAudio, miniaudio.
* **Frontend:** Tauri, React, TypeScript, Tailwind CSS.
* **AI APIs:** OpenAI (STT, LLM, Vision), ElevenLabs (TTS).

---

*This project is continuously evolving. Stay tuned for more features!*
