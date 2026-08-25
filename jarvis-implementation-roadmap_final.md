# 🤖 JARVIS — Full Implementation Roadmap

> এই ডকুমেন্টটা তৈরি করা হয়েছে যাতে সরাসরি **Claude Code / Codex / Antigravity**-কে দিয়ে শুরু থেকে শেষ পর্যন্ত phase-by-phase build করা যায়। প্রতিটা phase স্বাধীনভাবে কাজ করে, এবং প্রতিটা phase শেষে একটা "usable" Jarvis থাকবে।

---

## 🎯 Core Requirements (সব Phase-এ মাথায় রাখতে হবে)

1. **Wake Word** — একটা hidden/custom activation phrase বলে Jarvis-কে জাগানো যাবে (default word তুমি নিজে সেট করবে, কারো জানার দরকার নাই)
2. **Accent-aware STT (Input: যেকোনো ভাষা → Output: সবসময় English)** — তুমি বাংলায়, ইংরেজিতে, Banglish-এ বা মিক্স করে যাই বলো — Jarvis সব বুঝবে এবং সবসময় English-এ উত্তর দেবে। STT-এ কোনো language lock নেই, Bangladeshi accent সাপোর্ট করে।
3. **Wake Greeting** — "Hey Jarvis" বলার সাথে সাথে Jarvis একটা short cinematic sentence বলবে: *"Yes, sir. I'm online and ready. How can I assist you today?"*
4. **Original/Custom Voice** — Jarvis-এর নিজস্ব একটা voice থাকবে (generic robotic voice না)
5. **Confirmation for risky actions** — delete/shutdown/install ইত্যাদির আগে অনুমতি নেবে

---

## 🧱 Tech Stack (Final)

| Layer | Tool |
|---|---|
| Desktop shell | Tauri 2 |
| Frontend | React + TypeScript + Vite + Tailwind + Framer Motion + Three.js (React Three Fiber) + Zustand |
| Backend | Python + FastAPI + WebSocket + asyncio |
| Wake word | **openWakeWord** (free, open-source, custom wake word trainable) or **Picovoice Porcupine** (custom wake word console, free tier) |
| Speech-to-text | OpenAI **GPT Live Transcribe** (bilingual — Bangla + English hint দেওয়া যায়) |
| Text-to-speech | OpenAI **TTS** (voice select করা যায়) অথবা **ElevenLabs** (যদি বেশি natural/custom voice চাও, বাংলা সাপোর্টও ভালো) |
| AI reasoning | **GPT-5.6 Luna** (default), দরকার হলে **GPT-5.6 Terra** (edge-case জটিল planning) |
| Computer control | PyAutoGUI |
| Browser automation | Playwright |
| Memory (DB) | SQLite → পরে Qdrant/pgvector (semantic memory দরকার হলে) |

> **নোট (Voice নিয়ে):** OpenAI TTS-এর ready voice-গুলো বাংলায় খুব natural না-ও শোনাতে পারে। যদি Jarvis-কে সত্যিকারের "নিজস্ব" এবং বাংলায় স্পষ্ট voice দিতে চাও, Phase 2-তে ElevenLabs (multilingual + voice design/cloning সাপোর্ট করে) ব্যবহার করার অপশন রাখা হয়েছে — এটা Claude Code বানানোর সময় তোমাকে দুটো অপশনই try করতে দেবে।

### 🔑 Exact Model IDs (কোডে হুবহু এগুলো ব্যবহার করতে হবে)

| কাজ | Model ID |
|---|---|
| Reasoning/planning (default) | `gpt-5.6-luna` |
| Reasoning/planning (জটিল/edge-case) | `gpt-5.6-terra` |
| Voice-to-text (live) | `gpt-live-transcribe` |
| Text-to-speech | `tts-1` (অথবা ElevenLabs API ব্যবহার করলে ElevenLabs-এর নিজস্ব voice ID) |

> Claude Code-কে roadmap দেওয়ার সময় এই টেবিলটাও উল্লেখ করে দিও, যাতে ভুল/পুরনো model নাম (যেমন `gpt-4`, `gpt-3.5-turbo`) বসিয়ে না দেয়।

---

## 📁 Project Structure

```text
jarvis/
├── apps/
│   └── desktop/
│       ├── src/
│       │   ├── components/       # UI components (brain, panels, cards)
│       │   ├── features/         # voice, memory, conversation features
│       │   ├── stores/           # zustand state
│       │   └── lib/
│       └── src-tauri/
│
├── backend/
│   ├── api/                      # FastAPI routes + websocket
│   ├── core/                     # config, settings, env
│   ├── ai/                       # LLM routing (Luna/Terra), prompts
│   ├── voice/                    # wake word, STT, TTS
│   ├── memory/                   # SQLite models, memory read/write
│   ├── planner/                  # intent → tool-call planning
│   ├── vision/                   # (Phase 8) screen understanding
│   └── tools/
│       ├── apps/                 # open/close/switch app
│       ├── files/                # search/create/move/delete file
│       ├── browser/              # playwright actions
│       ├── system/               # volume/brightness/screenshot
│       └── automation/           # keyboard/mouse
│
├── shared/                       # shared types/schemas (frontend ↔ backend)
├── tests/
├── scripts/
├── .env
└── README.md
```

---

# 🗺️ PHASE-BY-PHASE ROADMAP

---

## Phase 0 — Foundation & Setup
**সময়: ১–২ দিন**

**Goal:** পুরো project skeleton, দুই দিক (frontend + backend) যেন একে অপরের সাথে কথা বলতে পারে।

**Tasks:**
- Tauri 2 + React + TypeScript + Vite + Tailwind project init
- Python FastAPI backend init, WebSocket endpoint বানানো
- Frontend ↔ Backend WebSocket connection টেস্ট করা (simple ping-pong message)
- `.env` structure বানানো এবং OpenAI API key load করা (ইতিমধ্যে key generate করা আছে ধরে নিয়ে):
  - `.env` ফাইলে `OPENAI_API_KEY=sk-xxxx` রাখা
  - `.env` অবশ্যই `.gitignore`-এ যোগ করা
  - backend startup-এ key load হয়ে একটা ছোট test call (`/v1/models`) সফল হচ্ছে কিনা check করা — fail করলে app শুরুতেই স্পষ্ট error দেখাবে, চুপচাপ fail করবে না
- Git repo + folder structure উপরের মতো বানানো

**Deliverable:** খালি একটা desktop window খুলবে, backend-এর সাথে connect হবে, console-এ "connected" দেখাবে।

**Claude Code প্রম্পট আইডিয়া:**
> "Set up a Tauri 2 + React + TypeScript + Vite + Tailwind desktop app, with a Python FastAPI backend that exposes a WebSocket endpoint. Connect the frontend to the backend WebSocket on app load and show a connection status indicator."

---

## Phase 1 — Jarvis UI
**সময়: ২–৪ দিন**

**Goal:** স্ক্রিনে Jarvis-কে দেখতে Jarvis-এর মতো লাগবে (functionality এখনো limited থাকবে)।

**Tasks:**
- Central "AI Brain" visual (Three.js/React Three Fiber দিয়ে animated core)
- Brain-এর states: Idle / Listening / Thinking / Executing / Speaking — প্রতিটার জন্য আলাদা animation
- System status panel (CPU/RAM/Network — dummy data দিয়ে শুরু করা যায়)
- Conversation panel (You/Jarvis message bubbles)
- Active Memory panel (static/dummy data দিয়ে শুরু)
- Zustand দিয়ে global UI state manage করা

**Deliverable:** UI সম্পূর্ণ দেখতে final Jarvis-এর মতো, কিন্তু state গুলো manually/dummy trigger করা যাবে।

---

## Phase 2 — Voice (Wake Word + STT + TTS, বাংলা+English)
**সময়: ৩–৫ দিন**

**Goal:** Custom wake word বলে Jarvis জাগানো, বাংলা/ইংরেজি দুই ভাষায় কথা শোনা এবং বলা।

**Tasks:**
1. **Wake word engine বসানো**
   - openWakeWord বা Picovoice Porcupine দিয়ে custom activation phrase train করা (তোমার পছন্দের গোপন phrase)
   - Background-এ সবসময় mic শুনবে শুধু wake word-এর জন্য (এটা local, কোনো API cost নাই)
   - Wake word detect হলেই → UI-তে "Listening" state trigger হবে + actual recording শুরু হবে
2. **Speech-to-Text**
   - Wake word-এর পর কথা রেকর্ড করে GPT Live Transcribe-এ পাঠানো
   - Language hint-এ `["bn", "en"]` দুটোই দেওয়া, যাতে বাংলা-ইংরেজি মেশানো কথাও ঠিকমতো ধরে
3. **Text-to-Speech**
   - OpenAI TTS দিয়ে শুরু করা (দ্রুত সেটআপ)
   - বাংলা voice quality কম মনে হলে ElevenLabs দিয়ে replace/test করা (custom voice বানানোর অপশনসহ)
   - উত্তর যে ভাষায় প্রশ্ন এসেছে, ডিফল্টভাবে সেই ভাষাতেই দেওয়া (settings-এ override করার অপশন রাখা)

**Deliverable:** Wake word বললে Jarvis সাড়া দেবে, বাংলা বা ইংরেজি যেকোনোটায় কথা বললে বুঝবে, এবং voice-এ জবাব দেবে।

**নিরাপত্তা নোট:** wake word phrase কোথাও plaintext config file-এ রাখলেও ঠিক আছে (এটা security secret না, misfire এড়ানোর জন্য শুধু)।

---

## Phase 3 — AI Brain (Intent Understanding + Planning)
**সময়: ২–৩ দিন**

**Goal:** যা শোনা গেছে সেটা থেকে বুঝা "এখন কী করতে হবে" এবং tool-call-এ রূপান্তর করা।

**Tasks:**
- GPT-5.6 Luna-কে system prompt দিয়ে সেট করা: "তুমি Jarvis, ব্যবহারকারীর কমান্ড বুঝে উপযুক্ত tool call বেছে নেবে"
- Function/tool calling schema বানানো (open_app, close_app, search_file, ইত্যাদির নাম ও parameter define করা — Phase 4/5/6-এ আসল tool যোগ হবে, এখন শুধু schema আর routing)
- Model routing logic: default Luna, কিন্তু task ambiguous/error-handling দরকার হলে Terra-তে fallback করার simple rule বসানো
- Response generation (tool result থেকে মানুষের ভাষায় উত্তর বানানো, বাংলা/ইংরেজি)
- **App-level cost/rate-limit guard:** OpenAI dashboard-এর monthly cap ছাড়াও backend-এ নিজস্ব guard রাখা —
  - দৈনিক token/request সংখ্যার একটা soft limit কোডে সেট করা (যেমন দিনে সর্বোচ্চ ৫০০ AI call)
  - Limit ছুঁয়ে গেলে Jarvis নিজেই বলবে "আজকের ব্যবহার limit শেষ, কাল আবার চেষ্টা করো" — চুপচাপ বেশি call চালিয়ে যাবে না
  - প্রতিটা API call-এর token usage log রাখা (SQLite-এ, Phase 7-এর memory DB-এর সাথেই)

**Deliverable:** তুমি বললে "Jarvis, ভলিউম কমাও" — এটা এখনো actual volume না কমালেও, backend log-এ দেখা যাবে AI সঠিক tool ও parameter বের করেছে।

**অফলাইন/API ডাউন হলে কী হবে (Fallback):**
- Internet না থাকলে বা OpenAI API down/error দিলে Jarvis silent freeze না হয়ে একটা local, hard-coded ভয়েস/টেক্সট রেসপন্স দেবে (যেমন: "এখন internet/AI সার্ভিসে সমস্যা হচ্ছে, একটু পরে আবার চেষ্টা করো")
- কিছু একদম basic command (volume, screenshot-এর মতো simple, non-AI action) চাইলে **offline rule-based shortcut** দিয়েও handle করা যায় (AI call ছাড়াই), যাতে internet না থাকলেও ন্যূনতম কাজ চলে — এটা optional, চাইলে পরে যোগ করা যাবে

---

## Phase 4 — Basic Computer Control
**সময়: ৩–৭ দিন**

**Goal:** প্রথমবারের মতো Jarvis সত্যিকারের কম্পিউটার কন্ট্রোল করবে।

**Tasks (PyAutoGUI দিয়ে):**
- `open_app(name)` / `close_app(name)` / `switch_app(name)`
- `type_text(text)` / `mouse_click(x, y)`
- `take_screenshot()`
- `set_volume(level)` / `set_brightness(level)`
- `get_system_info()`

প্রতিটা tool Phase 3-এর planner থেকে call হবে।

**Windows-specific নোট:** তুমি যেহেতু Windows-এ চালাবে —
- Volume control-এর জন্য শুধু PyAutoGUI যথেষ্ট না, সাথে **`pycaw`** লাইব্রেরি লাগবে (Windows audio API-এর সাথে সরাসরি কথা বলার জন্য)
- Brightness control-এর জন্য **`screen-brightness-control`** লাইব্রেরি লাগবে
- App খোলা/বন্ধ করার জন্য Windows-এ exact `.exe` path বা registered app name ঠিকমতো resolve করতে হবে (`os.startfile()` বা `subprocess` ব্যবহার করে) — Mac/Linux-এর command এখানে কাজ করবে না, তাই Claude Code-কে বলার সময় স্পষ্ট করে বলে দিও তুমি Windows ব্যবহার করছ

**Deliverable:** "Jarvis, notepad খোলো এবং Hello লিখো" — কাজটা সত্যিই হয়ে যাবে।

---

## Phase 5 — File System Control
**সময়: ২–৪ দিন**

**Tasks:**
- `search_file(query)` / `create_file()` / `move_file()` / `copy_file()` / `rename_file()` / `delete_file()`
- `read_file_summary()` (ছোট summarization)
- **Confirmation flow**: delete/move-এর মতো destructive action-এর আগে UI-তে confirmation popup পাঠানো (WebSocket দিয়ে frontend-এ "CONFIRM?" event পাঠিয়ে ইউজারের সাড়ার অপেক্ষা করা)

**Deliverable:** ফাইল খোঁজা/মুভ করা/ডিলিট করা voice দিয়ে করা যাবে, ঝুঁকিপূর্ণটাতে confirmation চাইবে।

---

## Phase 6 — Browser Automation
**সময়: ৩–৫ দিন**

**Tasks (Playwright দিয়ে):**
- `open_url(url)` / `search_web(query)`
- `youtube_search(query)`
- Basic form fill / tab switch tools
- Headed mode ব্যবহার করা যাতে browser action স্ক্রিনে visible থাকে

**Deliverable:** "Jarvis, YouTube-এ Python tutorial খোঁজো" — কাজটা সত্যিই ব্রাউজারে হবে।

---

## Phase 7 — Memory
**সময়: ৩–৫ দিন**

**Tasks:**
- SQLite schema: `users`, `conversations`, `preferences`, `tasks`, `activity_logs`
- প্রতি conversation turn memory-তে লগ হবে
- "Active Memory" panel real data থেকে populate হবে (current project, current app, recent intent)
- Planner-এ memory context inject করা (যাতে "আগের project-টা আবার খোলো" ধরনের কথা বুঝতে পারে)

**Deliverable:** Jarvis তোমার context মনে রাখবে, আগের কথার রেফারেন্স বুঝবে।

---

## Phase 8 — Agentic Multi-Step Tasks
**সময়: ৪–৭ দিন**

**Goal:** এক কমান্ডে সম্পূর্ণ workflow।

**Tasks:**
- Multi-step planner: একটা task-কে ধাপে ধাপে ভেঙে, প্রতিটা step execute করে, result দেখে পরের step ঠিক করা
- Error handling loop (কোনো step fail করলে retry/alternative বের করা — এখানেই Terra ব্যবহার করা যেতে পারে)
- Step-by-step progress UI-তে দেখানো ("Task: 3/5 steps complete")

**Deliverable:** "Jarvis, Ziranmart project চালু করে dev server রেডি করো" — পুরোটা নিজে নিজে হয়ে যাবে।

---

## Phase 9 — Vision (Visual Intelligence)
**সময়: ৫–৭ দিন**

**Tasks:**
- Screenshot নিয়ে vision-capable model-এ পাঠানো (কোন elements আছে বুঝতে)
- "কোথায় বাটন আছে" ধরনের প্রশ্নের উত্তর screen coordinate আকারে বের করা
- সেই coordinate ব্যবহার করে PyAutoGUI দিয়ে click করা
- UI-তে "Visual Intelligence" panel সচল করা (detected elements দেখানো)

**Deliverable:** Jarvis স্ক্রিন দেখে বুঝে কাজ করতে পারবে (শুধু text command না)।

---

## Phase 10 — Polish & Safety Hardening
**সময়: ২–৩ দিন**

**Tasks:**
- সব risky action (delete, shutdown, restart, install, send message) confirmation flow-এর আন্ডারে আছে কিনা double-check
- Error/exception handling সব tool-এ যোগ করা (silent fail না হয়ে বরং Jarvis বলবে "এটা করতে পারলাম না, কারণ...")
- Settings panel: wake word phrase, voice choice, ভাষা preference পরিবর্তনের UI
- Logging/activity history দেখার UI

**Deliverable:** Production-ready, নিরাপদ, ব্যবহারযোগ্য Jarvis v1।

---

# ✅ চূড়ান্ত Jarvis কী করতে পারবে (সব Phase শেষে)

- Custom hidden wake word বলে activate হবে
- বাংলা ও ইংরেজি — দুই ভাষাতেই কথা বুঝবে ও বলবে
- নিজস্ব custom voice-এ কথা বলবে
- App/file/system/browser control করবে voice কমান্ডে
- Multi-step কাজ (যেমন dev environment চালু করা) নিজে নিজে সম্পন্ন করবে
- Context/memory মনে রাখবে
- স্ক্রিন দেখে বুঝে কাজ করতে পারবে (vision)
- ঝুঁকিপূর্ণ কাজে অনুমতি চাইবে

---

# 💰 Budget আরেকবার সংক্ষেপে

| আইটেম | খরচ |
|---|---|
| Dev tools (সব ফ্রি) | ৳0 |
| Wake word engine (openWakeWord) | ৳0 (open-source) |
| Testing বাজেট (Phase 2 শুরুর পর থেকে) | ৳600–1,200 |
| প্রথম মাস normal ব্যবহার | ৳1,000–2,000 |

---

# 🚀 কীভাবে ব্যবহার করবে এই roadmap

এই পুরো ফাইলটা Claude Code / Codex / Antigravity-কে দিয়ে বলবে:

> "এই roadmap অনুযায়ী Phase 0 থেকে শুরু করো। প্রতিটা phase শেষে আমাকে জানাও এবং টেস্ট করার সুযোগ দাও, তারপর পরের phase-এ যাও।"

একবারে সব phase না করিয়ে, **phase ধরে ধরে এগোনোই ভালো** — এতে বাগ ধরা সহজ হবে এবং প্রতিটা ধাপে তুমি নিজে টেস্ট করে ফিডব্যাক দিতে পারবে।
