import json
from loguru import logger
from openai import AsyncOpenAI
from backend.core.config import settings
from backend.planner.schema import TOOLS_SCHEMA

SYSTEM_PROMPT = """
You are Jarvis, a highly intelligent and efficient AI assistant.
Your goal is to understand the user's command and choose the appropriate tool to execute it.
If the user's request requires an action (like opening an app, changing volume, etc.), use the provided tools.
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

    async def _call_llm(self, model: str, text: str) -> dict:
        """Helper to call OpenAI with a specific model and return the response."""
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            max_completion_tokens=300,
            extra_body={"reasoning_effort": "none"}
        )
        return response

    async def process_intent(self, text: str) -> str:
        """
        Process the user's text, extract intent, return a natural response.
        Implements fallback to Terra if Luna fails or acts ambiguously.
        """
        try:
            # 1. Try with default model (Luna)
            logger.info(f"🧠 AI Brain processing intent with {self.default_model}...")
            response = await self._call_llm(self.default_model, text)
            message = response.choices[0].message
            
            # Simple ambiguity check: if it refused to call a tool but the user clearly asked for action
            # (In a real app, this might be more sophisticated, but for now we fallback if it returns nothing useful)
            if not message.content and not message.tool_calls:
                raise ValueError("Ambiguous empty response from Luna")
                
            return self._handle_message(message)
            
        except Exception as e:
            logger.warning(f"⚠️ Luna model failed or ambiguous: {e}. Falling back to Terra ({self.fallback_model})...")
            try:
                # 2. Fallback to complex model (Terra)
                response = await self._call_llm(self.fallback_model, text)
                message = response.choices[0].message
                return self._handle_message(message)
            except Exception as e2:
                logger.error(f"❌ Terra fallback also failed: {e2}")
                # Offline/Fallback Hard-coded Response
                return "I'm having trouble connecting to my AI server. Please check your internet connection and try again."

    def _handle_message(self, message) -> str:
        """Parse tool calls for logging (Phase 3) and return the spoken response."""
        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                args = tool_call.function.arguments
                logger.success(f"🛠️ [Phase 3 Mock] AI decided to call tool: {func_name} with args: {args}")
            
            # Since we don't execute tools yet (Phase 3), log and return a brief English confirmation
            if message.content:
                return message.content
            else:
                return "Understood. I'll take care of that."
        else:
            return message.content or "I didn't quite catch that. Could you say that again?"
