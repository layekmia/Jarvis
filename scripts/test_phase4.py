import asyncio
from loguru import logger
from backend.ai.planner import AIBrain

async def main():
    brain = AIBrain()
    
    logger.info("Test 1: System info...")
    res = await brain.process_intent("What is my system info right now?")
    logger.info(f"Response: {res}")
    
    logger.info("Test 2: Open notepad and type something...")
    res = await brain.process_intent("Open notepad and type 'Hello World, Phase 4 is working!'")
    logger.info(f"Response: {res}")
    
    logger.info("Test 3: Close notepad...")
    res = await brain.process_intent("Close notepad")
    logger.info(f"Response: {res}")

if __name__ == "__main__":
    asyncio.run(main())
