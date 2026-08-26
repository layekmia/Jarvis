"""
Test script for Phase 8 (Agentic Multi-Step Tasks).
Tests: heuristic detection, LLM planning output, step execution, progress broadcasting.
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── 1. Heuristic detection tests ──────────────────────────────────────────────

from backend.ai.agentic_planner import AgenticPlanner

def test_heuristic():
    print("Testing heuristic multi-step detection...")

    multi_cases = [
        "Open Notepad then type Hello World",
        "Search YouTube for lofi music and then search Google for weather",
        "তারপর screenshot নাও",
        "Open Chrome, go to YouTube, then search for tutorials",
    ]
    single_cases = [
        "Open Notepad",
        "Set volume to 50",
        "Search YouTube for cats",
        "Close Chrome",
    ]
    ambiguous_cases = [
        "I need you to help me with something complex",
        "Prepare my workspace",
    ]

    for text in multi_cases:
        result = AgenticPlanner.is_multi_step(text)
        assert result is True, f"Expected True for: '{text}', got: {result}"
    print(f"  ✅ {len(multi_cases)} multi-step cases correctly detected")

    for text in single_cases:
        result = AgenticPlanner.is_multi_step(text)
        assert result is False, f"Expected False for: '{text}', got: {result}"
    print(f"  ✅ {len(single_cases)} single-step cases correctly detected")

    for text in ambiguous_cases:
        result = AgenticPlanner.is_multi_step(text)
        assert result is None, f"Expected None for: '{text}', got: {result}"
    print(f"  ✅ {len(ambiguous_cases)} ambiguous cases returned None (will use LLM judge)")


# ── 2. Step planning test ─────────────────────────────────────────────────────

async def test_planning():
    print("\nTesting step planning (requires backend/API)...")
    planner = AgenticPlanner()
    task = "Open Notepad and then type Hello World"
    steps = await planner.plan(task)

    assert len(steps) >= 2, f"Expected at least 2 steps, got {len(steps)}"
    assert all(s.tool for s in steps), "All steps must have a tool name"
    assert all(s.description for s in steps), "All steps must have a description"
    assert all(s.status == "pending" for s in steps), "All steps must start as pending"

    print(f"  ✅ Plan generated with {len(steps)} steps:")
    for s in steps:
        print(f"      Step {s.id}: [{s.tool}] {s.description}")


# ── 3. Step execution with mock tools ─────────────────────────────────────────

async def test_execution():
    print("\nTesting step execution with mock tools...")

    progress_events: list[dict] = []

    async def mock_broadcast(event: str, data: dict):
        if event == "task_progress":
            progress_events.append(data)

    async def mock_open_app(name: str) -> str:
        return f"Successfully opened {name}."

    def mock_type_text(text: str) -> str:
        return f"Typed: {text}"

    mock_tool_map = {
        "open_app": mock_open_app,
        "type_text": mock_type_text,
    }

    from backend.ai.agentic_planner import TaskStep
    steps = [
        TaskStep(id=1, description="Open Notepad", tool="open_app", args={"name": "Notepad"}),
        TaskStep(id=2, description="Type Hello World", tool="type_text", args={"text": "Hello World"}),
    ]

    planner = AgenticPlanner()
    result = await planner.run(
        task="Open Notepad and type Hello World",
        steps=steps,
        tool_map=mock_tool_map,
        tts_engine=None,
        player=None,
        broadcast_callback=mock_broadcast,
    )

    assert "complete" in result.lower() or "2" in result, f"Unexpected result: {result}"
    assert any(e.get("done") for e in progress_events), "Should have a 'done=True' event"
    assert all(s.status in ("done", "failed") for s in steps), "All steps must reach terminal state"

    print(f"  ✅ Execution completed: {result}")
    print(f"  ✅ {len(progress_events)} progress events broadcast")


# ── 4. Risky step detection ───────────────────────────────────────────────────

def test_risky_tools():
    print("\nTesting risky tool detection...")
    from backend.ai.agentic_planner import RISKY_TOOLS

    assert "delete_file" in RISKY_TOOLS
    assert "close_app" in RISKY_TOOLS
    assert "move_file" in RISKY_TOOLS
    assert "open_app" not in RISKY_TOOLS
    assert "set_volume" not in RISKY_TOOLS
    print(f"  ✅ RISKY_TOOLS correctly defined: {sorted(RISKY_TOOLS)}")


# ── Runner ────────────────────────────────────────────────────────────────────

async def main():
    print("🧪 Running Phase 8 Tests...\n")

    test_heuristic()
    await test_planning()
    await test_execution()
    test_risky_tools()

    print("\n🎉 ALL PHASE 8 TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
