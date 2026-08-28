"""
Check Conversation Context & History from jarvis_memory.db
Run:
    backend\.venv\Scripts\python.exe scripts\check_context.py
"""

import sys
import asyncio
from pathlib import Path
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.memory.db import init_db
from backend.memory.conversation_db import (
    init_conversation_db,
    get_recent_turns,
    get_latest_summary,
    get_turn_count,
)
from backend.ai.planner import AIBrain

def print_db_state():
    print("\n" + "=" * 60)
    print("📊 CURRENT CONVERSATION CONTEXT IN DATABASE")
    print("=" * 60)
    
    total_turns = get_turn_count()
    summary = get_latest_summary()
    recent = get_recent_turns(n=10)
    
    print(f"🔹 Total Stored Turns: {total_turns}")
    print(f"🔹 Latest Summary    : {summary if summary else '(None yet - not compressed)'}")
    print("\n📝 Last 10 Turns in DB:")
    if not recent:
        print("   (No conversation history yet)")
    else:
        for t in recent:
            role_icon = "👤" if t['role'] == "user" else "🤖"
            print(f"   {role_icon} [{t['role'].upper()}] ({t['timestamp']}): {t['content']}")
    print("=" * 60 + "\n")

async def test_live_context():
    print("\n🧪 TESTING LIVE MULTI-TURN CONTEXT CONTINUITY...")
    brain = AIBrain()
    
    # 1st Question
    q1 = "Hello! My favorite color is Neon Cyan."
    print(f"\n1️⃣ User: {q1}")
    res1 = await brain.process_intent(q1)
    print(f"   Jarvis: {res1}")
    
    # 2nd Question (Context Dependent - doesn't repeat color)
    q2 = "What was the color I just mentioned?"
    print(f"\n2️⃣ User: {q2}")
    res2 = await brain.process_intent(q2)
    print(f"   Jarvis: {res2}")
    
    print("\n✅ Verifying DB persistence after live test:")
    print_db_state()

if __name__ == "__main__":
    init_db()
    init_conversation_db()
    
    # Show current DB
    print_db_state()
    
    # Run test
    asyncio.run(test_live_context())
