import re
import json
from loguru import logger
from openai import AsyncOpenAI
from typing import Callable, Awaitable
from backend.core.config import settings
from backend.planner.schema import TOOLS_SCHEMA

# Phase 4 - Computer Control tools
from backend.tools.system import set_volume, set_brightness, get_system_info
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
}

SYSTEM_PROMPT = """
You are Jarvis, a highly intelligent and efficient AI assistant.
Your goal is to understand the user's command and choose the appropriate tool to execute it.
If the user's request requires an action (like opening an app, changing volume, etc.), use the provided tools.
You can chain multiple tools if needed (e.g., open app -> type text -> enter).
If no tool is applicable, just reply conversationally.

CRITICAL LANGUAGE INSTRUCTION:
The user may speak or type in English, Bengali, Banglish (Bengali written in English letters), or a mix of languages.
You must respond in the same language the user uses.
If the user speaks in English, reply in English.
If the user speaks in Bengali (Bangla) or Banglish, reply in Bengali but smartly mix English words where appropriate (Banglish / code-mixing) to sound natural and modern.
Keep your responses concise, professional, and friendly.

FILE SYSTEM SAFETY RULES:
- For delete_file, move_file, rename_file — the tool itself will return a confirmation prompt.
  You must relay that confirmation message to the user exactly and wait for their yes/no.
- Never skip the confirmation step for destructive file operations.
- Always use absolute Windows paths (e.g., C:/Users/layek/Desktop/file.txt).
"""


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
        """
        # ── Check if this message is a reply to a pending confirmation ────────
        text_lower = text.lower().strip()
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

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]

        try:
            logger.info(f"🧠 AI Brain processing intent with {self.default_model}...")
            response = await self._call_llm(self.default_model, messages)
            message = response.choices[0].message

            if not message.content and not message.tool_calls:
                raise ValueError("Ambiguous empty response from Luna")

            return await self._handle_message(message, messages, tts_engine, player, broadcast_callback)

        except Exception as e:
            logger.warning(f"⚠️ Luna model failed or ambiguous: {e}. Falling back to Terra ({self.fallback_model})...")
            try:
                response = await self._call_llm(self.fallback_model, messages)
                message = response.choices[0].message
                return await self._handle_message(message, messages, tts_engine, player, broadcast_callback)
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
            result = func(**args)
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

                # --- Step-by-Step Narration ---
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
                        result_str = TOOL_MAP[func_name](**args)
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

                # --- Completion Narration ---
                if tts_engine and player:
                    done_phrase = "Done."
                    if broadcast_callback:
                        await broadcast_callback("brain_state", {"state": "speaking"})
                    audio = await tts_engine.generate_speech(done_phrase)
                    await player.play_audio_async(audio)
                    if broadcast_callback:
                        await broadcast_callback("brain_state", {"state": "thinking"})

            # After all tools are executed, get final response from LLM
            final_response = await self._call_llm(self.default_model, messages)
            final_message = final_response.choices[0].message
            return final_message.content or "Task completed, sir."

        else:
            return message.content or "I didn't quite catch that. Could you say that again?"

    def _get_start_phrase(self, func_name: str, args: dict) -> str:
        """Returns a short, natural, bilingual start phrase for a tool."""
        if func_name == "open_app":
            return f"Opening {args.get('name', 'app')}, sir."
        elif func_name == "close_app":
            return f"বন্ধ করছি {args.get('name', 'app')}."
        elif func_name == "switch_app":
            return f"Switching to {args.get('name', 'the app')}."
        elif func_name == "set_volume":
            return "Adjusting volume."
        elif func_name == "type_text":
            return "লিখছি..."
        elif func_name == "take_screenshot":
            return "Taking a screenshot."
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
        else:
            return "Executing task."
