import asyncio
import sys
import os
from loguru import logger

# Add project root to path so backend imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ai.planner import AIBrain
from backend.memory.guard import RateLimitGuard
from backend.memory.db import init_db
from backend.memory.conversation_db import init_conversation_db

async def main():
    logger.info("Initializing Phase 3 Test (AI Brain + Guard)...")
    # Ensure DB tables exist (normally done by startup_event in main.py)
    init_db()
    init_conversation_db()
    
    guard = RateLimitGuard()
    brain = AIBrain()
    
    test_cases = [
        "Hey Jarvis, please open the calculator app.",
        "জার্ভিস, আমার জন্য একটু ভলিউম কমাও তো।",
        "Just say hello to me in Bengali.",
    ]
    
    for text in test_cases:
        logger.info(f"---")
        logger.info(f"🎤 Mock STT Input: '{text}'")
        
        try:
            guard.check_limit()
            response = await brain.process_intent(text)
            guard.log_usage(tokens=1)
            logger.success(f"🤖 Jarvis Response: {response}")
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
            
if __name__ == "__main__":
    asyncio.run(main())
