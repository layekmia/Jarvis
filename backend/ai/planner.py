import re
import json
import uuid
import asyncio
import inspect
from loguru import logger
from openai import AsyncOpenAI
from typing import Callable, Awaitable
from backend.core.config import settings
from backend.planner.schema import TOOLS_SCHEMA
from backend.memory.conversation_db import (
    append_turn,
    get_recent_turns,
    get_latest_summary,
    get_turn_count,
    save_summary,
)

# Phase 4 - Computer Control tools
from backend.tools.system import (
    set_volume, set_brightness, get_system_info,
    shutdown_system, shutdown_system_confirmed,
    restart_system, restart_system_confirmed,
)
from backend.tools.apps import open_app, close_app, switch_app
from backend.tools.interaction import type_text, mouse_click, take_screenshot

# Phase 5 - File System tools
from backend.tools.files.file_tools import (
    search_file,
    create_file,
    read_file_summary,
    copy_file,
    move_file,
    move_file_confirmed,
    rename_file,
    rename_file_confirmed,
    delete_file,
    delete_file_confirmed,
    list_directory,
    CONFIRM_PREFIX,
)

# Phase 6 - Browser Automation tools
from backend.tools.browser.browser_tools import (
    open_browser,
    open_url,
    open_new_tab,
    search_web,
    youtube_search,
    fill_form,
    switch_tab,
    close_browser,
)
from backend.tools.browser.youtube_tools import (
    youtube_play,
    youtube_open,
    youtube_search_chrome,
)

# Phase 7 - Memory tools
from backend.tools.memory.memory_tools import remember, forget
from backend.memory.db import get_all_memories

# Phase 8 - Agentic multi-step planner
from backend.ai.agentic_planner import AgenticPlanner

# Map tool names to actual python functions
TOOL_MAP = {
    # Phase 4
    "set_volume": set_volume,
    "set_brightness": set_brightness,
    "get_system_info": get_system_info,
    "open_app": open_app,
    "close_app": close_app,
    "switch_app": switch_app,
    "type_text": type_text,
    "mouse_click": mouse_click,
    "take_screenshot": take_screenshot,
    "shutdown_system": shutdown_system,
    "shutdown_system_confirmed": shutdown_system_confirmed,
    "restart_system": restart_system,
    "restart_system_confirmed": restart_system_confirmed,
    # Phase 5
    "search_file": search_file,
    "create_file": create_file,
    "read_file_summary": read_file_summary,
    "copy_file": copy_file,
    "move_file": move_file,
    "move_file_confirmed": move_file_confirmed,
    "rename_file": rename_file,
    "rename_file_confirmed": rename_file_confirmed,
    "delete_file": delete_file,
    "delete_file_confirmed": delete_file_confirmed,
    "list_directory": list_directory,
    # Phase 6
    "open_browser": open_browser,
    "open_url": open_url,
    "open_new_tab": open_new_tab,
    "search_web": search_web,
    "youtube_search": youtube_search_chrome,   # Chrome-based, uses correct profile
    "youtube_play": youtube_play,
    "youtube_open": youtube_open,
    "fill_form": fill_form,
    "switch_tab": switch_tab,
    "close_browser": close_browser,
    # Phase 7
    "remember": remember,
    "forget": forget,
}

# Phase 9 - Vision tools
from backend.tools.vision.vision_tools import describe_screen, click_element_on_screen
TOOL_MAP["describe_screen"] = describe_screen
TOOL_MAP["click_element_on_screen"] = click_element_on_screen

# Tools that should execute silently in the background without voice narration
SILENT_TOOLS = {
    "remember",
    "forget",
    "get_system_info",
    "list_directory",
    "read_file_summary"
}

from pathlib import Path as _Path
import os as _os

def _build_system_prompt() -> str:
    """Build system prompt with real runtime paths injected, so LLM never guesses usernames."""
    home = _Path.home()
    username = home.name
    return f"""
You are Jarvis, a highly intelligent and efficient AI assistant.
Your goal is to understand the user's command and choose the appropriate tool to execute it.
If the user's request requires an action (like opening an app, changing volume, etc.), use the provided tools.
You can chain multiple tools if needed (e.g., open app -> type text -> enter).
If no tool is applicable, just reply conversationally.

LANGUAGE INSTRUCTION:
The user may speak or type in English, Bengali, Banglish (Bengali written in English letters), or a mix.
You MUST ALWAYS reply in English only — regardless of what language the user uses.
Understand Bengali/Banglish input perfectly, but your response text must always be in English.
This is critical because the text-to-speech voice is an English voice and cannot pronounce Bengali properly.
Keep your responses concise, natural-sounding, and friendly.

FILE SYSTEM PATHS (use EXACTLY these — do NOT guess usernames or paths):
- Home directory  : {home}
- Desktop         : {home / 'Desktop'}
- Documents       : {home / 'Documents'}
- Downloads       : {home / 'Downloads'}
- Username        : {username}
- NEVER use paths like C:\\Users\\SomeOtherName\\ — always use the exact paths above.

POWER ACTIONS (REQUIRE CONFIRMATION):
- For shutdown_system and restart_system — the tool itself will return a confirmation prompt.
  You MUST relay that message to the user and wait for their explicit yes/no before anything happens.
- Never skip the confirmation step for shutdown or restart.

FILE SYSTEM SAFETY RULES:
- For delete_file, move_file, rename_file — the tool itself will return a confirmation prompt.
  You must relay that confirmation message to the user and wait for their yes/no.
- Never skip the confirmation step for destructive file operations.
- Always use absolute Windows paths with forward slashes, e.g. {home / 'Desktop' / 'file.txt'}.

MEMORY & CONTEXT RULES:
- If the user shares a preference, fact, or personal information (even without explicitly asking you to remember), you MUST spontaneously use the 'remember' tool to save it.
- Examples: "My name is John", "I like blue", "Use Chrome by default".
"""

# Build once at import time — real paths injected from the OS at startup
SYSTEM_PROMPT: str = _build_system_prompt()


def _parse_confirm_payload(result_str: str) -> dict[str, str]:
    """
    Parses the CONFIRM_NEEDED sentinel string and extracts the key=value pairs
    that encode the original tool call arguments and the action to execute.

    Example sentinel:
        CONFIRM_NEEDED: Move 'foo.txt' ... [source=C:/foo.txt|destination=C:/bar/foo.txt|action=move_file_confirmed]

    Returns a dict like:
        {"source": "C:/foo.txt", "destination": "C:/bar/foo.txt", "action": "move_file_confirmed"}
    """
    payload: dict[str, str] = {}
    match = re.search(r"\[(.+?)\]", result_str)
    if match:
        parts = match.group(1).split("|")
        for part in parts:
            if "=" in part:
                key, _, value = part.partition("=")
                payload[key.strip()] = value.strip()
    return payload


def _clean_url_for_speech(raw_url: str) -> str:
    """Extracts a clean, pronounceable name from a URL instead of reading raw https/slashes."""
    if not raw_url:
        return "the website"
    try:
        import urllib.parse
        u = raw_url if "://" in raw_url else "http://" + raw_url
        parsed = urllib.parse.urlparse(u)
        domain = parsed.netloc or parsed.path
        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        parts = domain.split(".")
        if len(parts) >= 2 and parts[0]:
            name = parts[0]
            special_names = {
                "chatgpt": "ChatGPT",
                "openai": "OpenAI",
                "youtube": "YouTube",
                "github": "GitHub",
                "google": "Google",
                "facebook": "Facebook",
                "twitter": "Twitter",
                "x": "X",
                "instagram": "Instagram",
                "linkedin": "LinkedIn",
                "reddit": "Reddit",
                "netflix": "Netflix",
                "spotify": "Spotify",
            }
            return special_names.get(name, name.capitalize())
        return domain.capitalize() if domain else "the website"
    except Exception:
        return "the website"


class AIBrain:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.default_model: str = settings.model_reasoning_default
        self.fallback_model: str = settings.model_reasoning_complex

        # Pending confirmations: maps a pending action key -> (func_name, args)
        self._pending_confirmation: dict[str, tuple[str, dict]] = {}

        # Persistent conversation — DB-backed sliding window.
        # session_id groups turns from the current app run so we can
        # display "this session" vs historical turns if needed in the future.
        self._session_id: str = str(uuid.uuid4())

        # How many raw turns (user+assistant each count as 1) to keep in the
        # LLM context window.  20 = ~10 back-and-forth exchanges.
        self._window_size: int = 20

        # When total raw turns in DB exceed this number, compress the older
        # half into a summary to avoid unbounded DB growth.
        self._compress_threshold: int = 30

        # Phase 8: Agentic planner instance (singleton per AIBrain)
        self.agentic_planner = AgenticPlanner()

    async def _call_llm(self, model: str, messages: list) -> dict:
        """Helper to call OpenAI with a specific model and return the response."""
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            max_completion_tokens=300,
            extra_body={"reasoning_effort": "none"}
        )
        return response

    async def _maybe_compress_history(self) -> None:
        """
        If total raw turns exceed _compress_threshold, summarise the older
        portion with a cheap LLM call and delete those raw rows from the DB.
        Keeps DB lean without losing conversational context.
        """
        total = get_turn_count()
        if total <= self._compress_threshold:
            return

        # Fetch all raw turns — we'll compress the older half
        all_turns = get_recent_turns(n=total)
        keep_count = self._window_size  # keep the freshest N turns raw
        to_compress = all_turns[:-keep_count] if len(all_turns) > keep_count else []

        if not to_compress:
            return

        # Build a mini-transcript for the summariser
        transcript = "\n".join(
            f"{t['role'].upper()}: {t['content']}" for t in to_compress
        )
        existing_summary = get_latest_summary()
        prior_context = (
            f"Previous summary: {existing_summary}\n\n" if existing_summary else ""
        )

        summarise_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a memory assistant. Summarise the following "
                    "conversation transcript into 2-3 concise sentences that "
                    "capture the key facts, user requests, and outcomes. "
                    "Be factual and dense — this will be injected as context."
                ),
            },
            {
                "role": "user",
                "content": f"{prior_context}Transcript to summarise:\n{transcript}",
            },
        ]

        try:
            resp = await self.client.chat.completions.create(
                model=self.default_model,
                messages=summarise_prompt,
                max_completion_tokens=150,
                extra_body={"reasoning_effort": "none"},
            )
            summary_text = resp.choices[0].message.content.strip()
            # covers_up_to_id is the DB id of the last row we compressed
            covers_up_to_id = to_compress[-1]["id"]
            save_summary(summary_text, covers_up_to_id)
            logger.info(f"💬 History compressed. Summary: {summary_text[:80]}...")
        except Exception as exc:
            logger.warning(f"⚠️  History compression failed (non-fatal): {exc}")

    def _get_context_messages(self, system_prompt: str) -> list[dict]:
        """
        Assemble the message list to send to the LLM:
          [system_prompt]
          + [optional: prior summary as a system note]
          + [last _window_size raw turns from DB]
        """
        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        # Inject summary (if any) so the LLM knows what happened before the window
        summary = get_latest_summary()
        if summary:
            messages.append({
                "role": "system",
                "content": f"[PRIOR CONVERSATION SUMMARY]\n{summary}",
            })

        # Append the sliding window of raw turns
        recent = get_recent_turns(n=self._window_size)
        for turn in recent:
            messages.append({"role": turn["role"], "content": turn["content"]})

        return messages

    async def process_intent(
        self,
        text: str,
        tts_engine=None,
        player=None,
        broadcast_callback: Callable[[str, dict], Awaitable[None]] = None
    ) -> str:
        """
        Process the user's text, extract intent, and execute tools dynamically.
        Handles confirmation flow for destructive file operations.
        Implements fallback to Terra if Luna fails.
        Delegates to AgenticPlanner for detected multi-step tasks.
        """
        text_lower = text.lower().strip()

        # ── Check if resuming an agentic task after a risky step confirmation ──
        if self.agentic_planner._awaiting_confirmation:
            confirmed = any(w in text_lower for w in ["yes", "confirm", "ok", "হ্যাঁ", "হ", "করো", "do it"])
            denied = any(w in text_lower for w in ["no", "cancel", "stop", "না", "বাদ দাও", "don't", "skip"])
            if confirmed or denied:
                return await self.agentic_planner.resume_after_confirmation(
                    confirmed=confirmed,
                    tool_map=TOOL_MAP,
                    tts_engine=tts_engine,
                    player=player,
                    broadcast_callback=broadcast_callback,
                )

        # ── Check if this message is a reply to a pending single-step confirmation ─
        if self._pending_confirmation:
            confirmed = any(w in text_lower for w in ["yes", "confirm", "ok", "হ্যাঁ", "হ", "করো", "do it"])
            denied = any(w in text_lower for w in ["no", "cancel", "stop", "না", "বাদ দাও", "don't"])

            if confirmed or denied:
                return await self._handle_pending_confirmation(
                    confirmed=confirmed,
                    tts_engine=tts_engine,
                    player=player,
                    broadcast_callback=broadcast_callback,
                )

        # ── Check for Introduction / Identity questions ─────────────────────────
        intro_triggers = [
            "who are you", "who r u", "introduce yourself", "tell me about yourself",
            "who made you", "who created you", "tumi ke", "tomar porichoy", "তোমার পরিচয়",
            "তোমার পরিচয়"
        ]
        if any(trigger in text_lower for trigger in intro_triggers):
            intro_speech = (
                "Allow me to introduce myself. I am JARVIS, a personal artificial intelligence "
                "assistant designed by Layek to manage your workspace and digital operations. "
                "All systems are fully initialized and operating at peak performance. "
                "How may I assist you today, sir?"
            )
            append_turn(self._session_id, "user", text)
            append_turn(self._session_id, "assistant", intro_speech)
            return intro_speech

        # ── Phase 8: Multi-step detection (heuristic-first, LLM judge as fallback) ─
        heuristic_result = AgenticPlanner.is_multi_step(text)
        if heuristic_result is None:
            # Ambiguous — use one LLM judge call
            heuristic_result = await self.agentic_planner.judge_multi_step(text)

        if heuristic_result:
            logger.info("[Agentic] Multi-step task detected — delegating to AgenticPlanner.")
            if broadcast_callback:
                await broadcast_callback("brain_state", {"state": "thinking"})
            steps = await self.agentic_planner.plan(text)
            if steps:
                result = await self.agentic_planner.run(
                    task=text,
                    steps=steps,
                    tool_map=TOOL_MAP,
                    tts_engine=tts_engine,
                    player=player,
                    broadcast_callback=broadcast_callback,
                )
                # Persist to conversation DB
                append_turn(self._session_id, "user", text)
                append_turn(self._session_id, "assistant", result)
                await self._maybe_compress_history()
                if result.startswith("__AGENTIC_AWAITING_CONFIRM__"):
                    # Risky step paused — return nothing (confirmation narrated already)
                    return ""
                return result
            # If planning returned no steps, fall through to normal single-step flow

        # ── 1. Fetch Explicit Memories ─────────────────────────────────────────
        memories = get_all_memories()
        memory_str = "\n".join([f"- [{m['category'].upper()}] {m['label']}: {m['value']}" for m in memories])
        if memory_str:
            memory_context = f"\n\n--- ACTIVE MEMORY (FACTS & PREFERENCES) ---\n{memory_str}\n(Update this using 'remember' or 'forget' tools if needed)."
        else:
            memory_context = "\n\n--- ACTIVE MEMORY ---\nEmpty. (Use 'remember' tool spontaneously when user shares facts/preferences)."

        dynamic_system_prompt = SYSTEM_PROMPT + memory_context

        # ── 2. Assemble Messages — DB-backed sliding window ────────────────────
        # _get_context_messages() returns [system] + [summary?] + [last N raw turns]
        # We then append the current user turn at the end.
        messages = self._get_context_messages(dynamic_system_prompt)
        messages.append({"role": "user", "content": text})

        try:
            logger.info(f"🧠 AI Brain processing intent with {self.default_model}...")
            response = await self._call_llm(self.default_model, messages)
            message = response.choices[0].message

            if not message.content and not message.tool_calls:
                raise ValueError("Ambiguous empty response from Luna")

            final_response_text = await self._handle_message(message, messages, tts_engine, player, broadcast_callback)

            # Persist to conversation DB (both sides of the exchange)
            append_turn(self._session_id, "user", text)
            append_turn(self._session_id, "assistant", final_response_text)
            # Opportunistically compress old history (cheap, non-blocking)
            await self._maybe_compress_history()

            return final_response_text

        except Exception as e:
            logger.warning(f"⚠️ Luna model failed or ambiguous: {e}. Falling back to Terra ({self.fallback_model})...")
            try:
                response = await self._call_llm(self.fallback_model, messages)
                message = response.choices[0].message
                final_response_text = await self._handle_message(message, messages, tts_engine, player, broadcast_callback)

                # Persist to conversation DB
                append_turn(self._session_id, "user", text)
                append_turn(self._session_id, "assistant", final_response_text)
                await self._maybe_compress_history()

                return final_response_text
            except Exception as e2:
                logger.error(f"❌ Terra fallback also failed: {e2}")
                return "I'm having trouble connecting to my AI server. Please check your internet connection and try again."

    async def _handle_pending_confirmation(
        self,
        confirmed: bool,
        tts_engine=None,
        player=None,
        broadcast_callback: Callable[[str, dict], Awaitable[None]] = None,
    ) -> str:
        """Execute or cancel a pending destructive action based on user's yes/no."""
        # Take the first pending confirmation
        action_key, (func_name, args) = next(iter(self._pending_confirmation.items()))
        self._pending_confirmation.clear()

        if not confirmed:
            logger.info(f"User cancelled action: {func_name}")
            return "Understood. I've cancelled the action."

        # Execute the confirmed action
        func = TOOL_MAP.get(func_name)
        if not func:
            return f"I couldn't find the action to execute: {func_name}."

        try:
            logger.info(f"🛠️ Executing confirmed action: {func_name} with {args}")
            if broadcast_callback:
                await broadcast_callback("brain_state", {"state": "executing"})
            tool_func = func
            if inspect.iscoroutinefunction(tool_func):
                result = await tool_func(**args)
            else:
                result = await asyncio.to_thread(tool_func, **args)
            logger.success(f"Confirmed action completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing confirmed action {func_name}: {e}")
            return f"Something went wrong while executing the action: {str(e)}"

    async def _handle_message(
        self,
        message,
        messages: list,
        tts_engine,
        player,
        broadcast_callback: Callable[[str, dict], Awaitable[None]] = None
    ) -> str:
        """Parse tool calls, narrate actions, execute them, and return the spoken response."""
        if message.tool_calls:
            messages.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name

                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                logger.success(f"🛠️ AI deciding to call tool: {func_name} with args: {args}")

                is_silent = func_name in SILENT_TOOLS

                # --- Step-by-Step Narration ---
                if not is_silent:
                    start_phrase = self._get_start_phrase(func_name, args)
                    if tts_engine and player:
                        if broadcast_callback:
                            await broadcast_callback("brain_state", {"state": "speaking"})
                        audio = await tts_engine.generate_speech(start_phrase)
                        await player.play_audio_async(audio)
                        if broadcast_callback:
                            await broadcast_callback("brain_state", {"state": "thinking"})

                # --- Execute Tool ---
                result_str = "Error: Tool not found."
                if func_name in TOOL_MAP:
                    try:
                        tool_func = TOOL_MAP[func_name]
                        # If the tool is a native coroutine (async), await it directly.
                        # Otherwise, run it in a thread to avoid blocking the event loop.
                        if inspect.iscoroutinefunction(tool_func):
                            result_str = await tool_func(**args)
                        else:
                            result_str = await asyncio.to_thread(tool_func, **args)
                    except Exception as e:
                        result_str = f"Error executing tool: {e}"
                        logger.error(result_str)
                else:
                    logger.warning(f"Tool {func_name} is not implemented in TOOL_MAP.")

                # ── Check if this is a confirmation request ────────────────
                if isinstance(result_str, str) and result_str.startswith(CONFIRM_PREFIX):
                    payload = _parse_confirm_payload(result_str)
                    confirmed_action = payload.pop("action", None)

                    if confirmed_action:
                        # Store pending confirmation
                        self._pending_confirmation["pending"] = (confirmed_action, payload)
                        # Strip sentinel prefix for user-facing message
                        user_msg = result_str[len(CONFIRM_PREFIX):].strip()
                        # Remove the bracketed metadata
                        user_msg = re.sub(r"\s*\[.+?\]", "", user_msg).strip()
                        logger.info(f"Confirmation required for: {confirmed_action}")
                        return user_msg

                # Append tool result to history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": result_str
                })

            # After all tools are executed, get final response from LLM
            final_response = await self._call_llm(self.default_model, messages)
            final_message = final_response.choices[0].message
            return final_message.content or "Done, boss."

        else:
            return message.content or "I didn't quite catch that. Could you say that again?"

    def _get_start_phrase(self, func_name: str, args: dict) -> str:
        """Returns a short, natural, clean start phrase for a tool."""
        if func_name == "open_app":
            return f"Opening {args.get('name', 'app')}..."
        elif func_name == "close_app":
            return f"Closing {args.get('name', 'app')}..."
        elif func_name == "switch_app":
            return f"Switching to {args.get('name', 'the app')}..."
        elif func_name == "set_volume":
            return "Adjusting volume..."
        elif func_name == "type_text":
            return "Typing..."
        elif func_name == "take_screenshot":
            return "Taking a screenshot..."
        elif func_name == "search_file":
            return f"Searching for '{args.get('query', 'files')}'..."
        elif func_name == "create_file":
            return "Creating the file..."
        elif func_name == "read_file_summary":
            return "Reading the file..."
        elif func_name == "copy_file":
            return "Copying..."
        elif func_name == "move_file":
            return "Checking if it's safe to move..."
        elif func_name == "rename_file":
            return "Checking rename..."
        elif func_name == "delete_file":
            return "Checking before deletion..."
        elif func_name == "list_directory":
            return "Listing directory contents..."
        elif func_name == "open_browser":
            return "Opening browser..."
        elif func_name == "open_url":
            site_name = _clean_url_for_speech(args.get('url', ''))
            return f"Opening {site_name}..."
        elif func_name == "open_new_tab":
            site_name = _clean_url_for_speech(args.get('url', ''))
            return f"Opening {site_name} in a new tab..." if site_name != "the website" else "Opening a new tab..."
        elif func_name == "search_web":
            return "Searching the web..."
        elif func_name == "youtube_search":
            return "Searching YouTube..."
        elif func_name == "youtube_play":
            return f"Playing {args.get('query', 'video')} on YouTube..."
        elif func_name == "youtube_open":
            return "Opening YouTube..."
        elif func_name == "fill_form":
            return "Filling the form..."
        elif func_name == "switch_tab":
            return "Switching tabs..."
        elif func_name == "close_browser":
            return "Closing the browser..."
        else:
            return "Executing task..."

