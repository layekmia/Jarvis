import json
from loguru import logger
from openai import AsyncOpenAI
from backend.core.config import settings
from backend.planner.schema import TOOLS_SCHEMA

SYSTEM_PROMPT = """
You are Jarvis, a highly intelligent and helpful AI assistant.
Your goal is to understand the user's command and choose the appropriate tool to execute it.
If the user's request requires an action (like opening an app, changing volume, etc.), use the provided tools.
If no tool is applicable, just reply conversationally.

CRITICAL INSTRUCTION FOR LANGUAGE:
You must ALWAYS respond in the EXACT same language that the user used. 
If the user speaks in Bengali, you must reply in natural Bengali script.
If the user speaks in English, you must reply in English.
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
                return "আমি এখন ইন্টারনেটের সাথে যুক্ত নই অথবা আমার এআই সার্ভারে সমস্যা হচ্ছে। একটু পরে আবার চেষ্টা করো।"

    def _handle_message(self, message) -> str:
        """Parse tool calls for logging (Phase 3) and return the spoken response."""
        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                args = tool_call.function.arguments
                logger.success(f"🛠️ [Phase 3 Mock] AI decided to call tool: {func_name} with args: {args}")
            
            # Since we don't execute tools in Phase 3, we generate a static response if the AI didn't provide one
            if message.content:
                return message.content
            else:
                return "ঠিক আছে, আমি করে দিচ্ছি।" # "Alright, I'll do it."
        else:
            return message.content or "আমি ঠিক বুঝতে পারলাম না।"
