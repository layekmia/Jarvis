import json
from loguru import logger
from openai import AsyncOpenAI
from typing import Callable, Awaitable
from backend.core.config import settings
from backend.planner.schema import TOOLS_SCHEMA

# Import all tools
from backend.tools.system import set_volume, set_brightness, get_system_info
from backend.tools.apps import open_app, close_app, switch_app
from backend.tools.interaction import type_text, mouse_click, take_screenshot

# Map tool names to actual python functions
TOOL_MAP = {
    "set_volume": set_volume,
    "set_brightness": set_brightness,
    "get_system_info": get_system_info,
    "open_app": open_app,
    "close_app": close_app,
    "switch_app": switch_app,
    "type_text": type_text,
    "mouse_click": mouse_click,
    "take_screenshot": take_screenshot,
}

SYSTEM_PROMPT = """
You are Jarvis, a highly intelligent and efficient AI assistant.
Your goal is to understand the user's command and choose the appropriate tool to execute it.
If the user's request requires an action (like opening an app, changing volume, etc.), use the provided tools.
You can chain multiple tools if needed (e.g., open app -> type text -> enter).
If no tool is applicable, just reply conversationally.

CRITICAL LANGUAGE INSTRUCTION:
The user may speak or type in English, Bengali, Banglish (Bengali written in English letters), or a mix of languages.
No matter what language or dialect the user uses — you MUST ALWAYS reply in English only.
Never respond in Bengali script or any other language. English-only responses at all times.
Keep your responses concise, professional, and friendly.
"""

class AIBrain:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.default_model = settings.model_reasoning_default
        self.fallback_model = settings.model_reasoning_complex

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
        Implements fallback to Terra if Luna fails.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
        
        try:
            # 1. Try with default model (Luna)
            logger.info(f"🧠 AI Brain processing intent with {self.default_model}...")
            response = await self._call_llm(self.default_model, messages)
            message = response.choices[0].message
            
            if not message.content and not message.tool_calls:
                raise ValueError("Ambiguous empty response from Luna")
                
            return await self._handle_message(message, messages, tts_engine, player, broadcast_callback)
            
        except Exception as e:
            logger.warning(f"⚠️ Luna model failed or ambiguous: {e}. Falling back to Terra ({self.fallback_model})...")
            try:
                # 2. Fallback to complex model (Terra)
                response = await self._call_llm(self.fallback_model, messages)
                message = response.choices[0].message
                return await self._handle_message(message, messages, tts_engine, player, broadcast_callback)
            except Exception as e2:
                logger.error(f"❌ Terra fallback also failed: {e2}")
                return "I'm having trouble connecting to my AI server. Please check your internet connection and try again."

    async def _handle_message(self, message, messages: list, tts_engine, player, broadcast_callback) -> str:
        """Parse tool calls, narrate actions, execute them, and return the spoken response."""
        if message.tool_calls:
            # We append the assistant's tool call intent to the history
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
                        # Execute the python function with the args
                        result_str = TOOL_MAP[func_name](**args)
                    except Exception as e:
                        result_str = f"Error executing tool: {e}"
                        logger.error(result_str)
                else:
                    logger.warning(f"Tool {func_name} is not implemented in TOOL_MAP.")

                # Append tool result to history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": result_str
                })
                
                # --- Completion Narration (Optional: done for multi-step tasks) ---
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
            app_name = args.get("name", "app")
            return f"Opening {app_name}, sir."
        elif func_name == "close_app":
            app_name = args.get("name", "app")
            return f"বন্ধ করছি {app_name}."
        elif func_name == "switch_app":
            return f"Switching to {args.get('name', 'the app')}."
        elif func_name == "set_volume":
            return "Adjusting volume."
        elif func_name == "type_text":
            return "লিখছি..."
        elif func_name == "take_screenshot":
            return "Taking a screenshot."
        else:
            return "Executing task."
