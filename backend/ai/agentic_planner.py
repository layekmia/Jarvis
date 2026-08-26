"""
Phase 8 — Agentic Multi-Step Task Planner

Breaks down complex voice commands into sequential steps and executes them
one by one, broadcasting real-time progress to the frontend via WebSocket.

Key design decisions:
- Heuristic-first routing: no LLM judge call for clearly simple/multi commands
- Risky steps (delete/close_app) pause the task and await user confirmation
- Step failures narrate the error and continue (no silent failures)
"""

import json
import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Optional
from loguru import logger

from backend.core.config import settings
from openai import AsyncOpenAI

# ── Constants ──────────────────────────────────────────────────────────────────

# Keywords that strongly suggest a multi-step intent (checked via heuristic first)
MULTI_STEP_KEYWORDS: list[str] = [
    " then ", " and then ", " after that ", " also ", " next ", " finally ",
    " first ", " second ", " third ", " afterwards ", " subsequently ",
    # Bengali / Banglish equivalents (no space guards — Bengali starts sentences with these)
    "তারপর", "তারপরে", "এরপর", "এবং তারপর", "শেষে",
    " taarpor ", " tar por ", " erpor ", " tarpor ",
]

# Keywords that firmly indicate a single, direct command (never multi-step)
SINGLE_STEP_INDICATORS: list[str] = [
    "open ", "close ", "set ", "search ", "play ", "take ", "show ",
    "type ", "click ", "go to ", "launch ", "start ",
]

# Tool names that require user confirmation before executing (from Phase 5 risky actions)
RISKY_TOOLS: frozenset[str] = frozenset({
    "delete_file",
    "delete_file_confirmed",
    "move_file",
    "move_file_confirmed",
    "rename_file",
    "rename_file_confirmed",
    "close_app",
    "shutdown_system",
    "restart_system",
})

# System prompt for the step-planning LLM call
PLAN_SYSTEM_PROMPT = """You are Jarvis's task planner. The user gave a multi-step command.
Break it into sequential steps. Return ONLY a valid JSON array, no markdown, no explanation.

Each step object must have:
- "description": a short human-readable sentence (e.g. "Open Notepad")
- "tool": the tool name to call (must be one of the available tools)
- "args": an object with the tool's arguments

Available tools: open_app, close_app, switch_app, set_volume, set_brightness,
get_system_info, type_text, mouse_click, take_screenshot, shutdown_system, restart_system,
search_file, create_file, read_file_summary, copy_file, move_file,
rename_file, delete_file, list_directory,
open_url, search_web, youtube_search, youtube_play, youtube_open,
fill_form, switch_tab, close_browser,
remember, forget, describe_screen, click_element_on_screen

Example output:
[
  {"description": "Open Notepad", "tool": "open_app", "args": {"name": "Notepad"}},
  {"description": "Type Hello World", "tool": "type_text", "args": {"text": "Hello World"}}
]

IMPORTANT: Return ONLY the JSON array. No extra text.
"""


@dataclass
class TaskStep:
    """Represents one step in an agentic task plan."""
    id: int
    description: str
    tool: str
    args: dict
    status: str = "pending"   # pending | running | done | failed | awaiting_confirmation


class AgenticPlanner:
    """
    Plans and executes multi-step tasks sequentially.
    Broadcasts task_progress events to the frontend at each step.
    Risky steps pause and await user confirmation before proceeding.
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.default_model: str = settings.model_reasoning_default
        self.fallback_model: str = settings.model_reasoning_complex

        # If a risky step is pending user yes/no, it's stored here
        self._awaiting_confirmation: Optional[tuple[list[TaskStep], int,
                                                    Callable, object, object, Callable]] = None

    # ── Public API ─────────────────────────────────────────────────────────────

    @staticmethod
    def is_multi_step(text: str) -> Optional[bool]:
        """
        Heuristic check for multi-step intent.
        Returns True (definitely multi), False (definitely single), or None (ambiguous).
        Only ambiguous cases escalate to an LLM judge.
        """
        lower = text.lower()

        # If any multi-step keyword is found → multi
        for kw in MULTI_STEP_KEYWORDS:
            if kw in lower:
                logger.debug(f"[Agentic] Multi-step keyword '{kw.strip()}' detected.")
                return True

        # If the command is very short and starts with a single-step indicator → single
        words = lower.split()
        if len(words) <= 6:
            for indicator in SINGLE_STEP_INDICATORS:
                if lower.startswith(indicator):
                    logger.debug("[Agentic] Short single-step command detected via heuristic.")
                    return False

        # Ambiguous — let the LLM decide
        return None

    async def judge_multi_step(self, text: str) -> bool:
        """
        Calls the LLM ONLY when heuristic is inconclusive (None).
        Returns True if multi-step, False if single-step.
        One lightweight call to save rate-limit quota.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Is the following user command a multi-step task requiring several sequential actions "
                            "(e.g. open app THEN type text), or is it a single action? "
                            "Reply with ONLY the word: MULTI or SINGLE."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                max_completion_tokens=5,
                extra_body={"reasoning_effort": "none"},
            )
            verdict = response.choices[0].message.content.strip().upper()
            is_multi = verdict == "MULTI"
            logger.info(f"[Agentic] LLM judge verdict: {verdict} → is_multi={is_multi}")
            return is_multi
        except Exception as e:
            logger.warning(f"[Agentic] LLM judge failed ({e}), defaulting to single-step.")
            return False

    async def plan(self, task: str) -> list[TaskStep]:
        """
        Asks the LLM to break the task into steps.
        Returns a list of TaskStep objects.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                    {"role": "user", "content": task},
                ],
                max_completion_tokens=600,
                extra_body={"reasoning_effort": "none"},
            )
            raw = response.choices[0].message.content or "[]"
            # Strip any accidental markdown fences
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            steps_data: list[dict] = json.loads(raw)

            steps = [
                TaskStep(
                    id=i + 1,
                    description=s.get("description", f"Step {i+1}"),
                    tool=s.get("tool", ""),
                    args=s.get("args", {}),
                )
                for i, s in enumerate(steps_data)
                if s.get("tool")
            ]
            logger.info(f"[Agentic] Planned {len(steps)} steps for: '{task}'")
            return steps

        except Exception as e:
            logger.error(f"[Agentic] Planning failed: {e}")
            return []

    async def run(
        self,
        task: str,
        steps: list[TaskStep],
        tool_map: dict,
        tts_engine,
        player,
        broadcast_callback: Callable[[str, dict], Awaitable[None]],
    ) -> str:
        """
        Executes all steps sequentially.
        Pauses on risky steps and awaits user confirmation.
        Broadcasts task_progress at every step transition.
        """
        total = len(steps)
        completed = 0
        results: list[str] = []

        for step in steps:
            step.status = "running"
            await self._broadcast_progress(broadcast_callback, steps, step, total)

            # ── Risky step: pause and ask user to confirm ──────────────────────
            if step.tool in RISKY_TOOLS:
                step.status = "awaiting_confirmation"
                await self._broadcast_progress(broadcast_callback, steps, step, total)

                confirm_msg = (
                    f"Step {step.id}: '{step.description}' is a potentially risky action. "
                    f"Should I proceed? Say 'yes' to continue or 'no' to skip this step."
                )
                # Store state so process_intent can resume after user answers
                self._awaiting_confirmation = (steps, step.id, tool_map, tts_engine, player, broadcast_callback)

                if tts_engine and player:
                    audio = await tts_engine.generate_speech(confirm_msg)
                    await player.play_audio_async(audio)

                return f"__AGENTIC_AWAITING_CONFIRM__:{step.id}"

            # ── Normal step: execute ───────────────────────────────────────────
            result = await self._execute_step(step, tool_map)
            results.append(result)
            completed += 1

            if "Error" in result or "Failed" in result:
                step.status = "failed"
                logger.warning(f"[Agentic] Step {step.id} failed: {result}")
                # Narrate failure but continue
                if tts_engine and player:
                    await broadcast_callback("brain_state", {"state": "speaking"})
                    audio = await tts_engine.generate_speech(
                        f"Step {step.id} failed: {result}. Continuing with next step."
                    )
                    await player.play_audio_async(audio)
                    await broadcast_callback("brain_state", {"state": "thinking"})
            else:
                step.status = "done"

            await self._broadcast_progress(broadcast_callback, steps, step, total)

        # All steps done
        await broadcast_callback("task_progress", {
            "done": True,
            "total": total,
            "completed": completed,
            "steps": self._steps_to_dict(steps),
        })

        summary = f"Task complete. Executed {completed} of {total} steps."
        logger.success(f"[Agentic] {summary}")
        return summary

    async def resume_after_confirmation(
        self,
        confirmed: bool,
        tool_map: dict,
        tts_engine,
        player,
        broadcast_callback: Callable[[str, dict], Awaitable[None]],
    ) -> str:
        """Called by process_intent when user answers yes/no to a risky step."""
        if not self._awaiting_confirmation:
            return "No pending task to resume."

        steps, pending_step_id, _, _, _, _ = self._awaiting_confirmation
        self._awaiting_confirmation = None

        total = len(steps)
        completed = sum(1 for s in steps if s.status == "done")

        for step in steps:
            if step.id < pending_step_id:
                continue

            if step.id == pending_step_id:
                if not confirmed:
                    step.status = "failed"
                    await self._broadcast_progress(broadcast_callback, steps, step, total)
                    logger.info(f"[Agentic] User skipped risky step {step.id}.")
                    # Continue with the rest
                    continue
                else:
                    # Execute the confirmed risky step
                    step.status = "running"
                    await self._broadcast_progress(broadcast_callback, steps, step, total)
                    result = await self._execute_step(step, tool_map)
                    step.status = "done" if "Error" not in result and "Failed" not in result else "failed"
                    completed += 1
                    await self._broadcast_progress(broadcast_callback, steps, step, total)
                    continue

            # Execute remaining normal steps
            if step.status == "pending":
                step.status = "running"
                await self._broadcast_progress(broadcast_callback, steps, step, total)
                result = await self._execute_step(step, tool_map)
                step.status = "done" if "Error" not in result and "Failed" not in result else "failed"
                completed += 1
                await self._broadcast_progress(broadcast_callback, steps, step, total)

        await broadcast_callback("task_progress", {
            "done": True,
            "total": total,
            "completed": completed,
            "steps": self._steps_to_dict(steps),
        })
        return f"Task resumed and completed. {completed}/{total} steps done."

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _execute_step(self, step: TaskStep, tool_map: dict) -> str:
        """Runs the tool for a single step and returns its result string."""
        tool_fn = tool_map.get(step.tool)
        if tool_fn is None:
            msg = f"Error: tool '{step.tool}' not found."
            logger.error(f"[Agentic] {msg}")
            return msg

        try:
            logger.info(f"[Agentic] Executing step {step.id}: {step.description}")
            if inspect.iscoroutinefunction(tool_fn):
                return await tool_fn(**step.args)
            else:
                return await asyncio.to_thread(tool_fn, **step.args)
        except Exception as e:
            msg = f"Error executing '{step.tool}': {e}"
            logger.error(f"[Agentic] {msg}")
            return msg

    async def _broadcast_progress(
        self,
        broadcast_callback: Callable,
        all_steps: list[TaskStep],
        current_step: TaskStep,
        total: int,
    ) -> None:
        """Broadcasts a task_progress event to the frontend."""
        try:
            await broadcast_callback("task_progress", {
                "done": False,
                "current": current_step.id,
                "total": total,
                "currentDescription": current_step.description,
                "currentStatus": current_step.status,
                "steps": self._steps_to_dict(all_steps),
            })
        except Exception as e:
            logger.warning(f"[Agentic] Failed to broadcast progress: {e}")

    @staticmethod
    def _steps_to_dict(steps: list[TaskStep]) -> list[dict]:
        return [
            {
                "id": s.id,
                "description": s.description,
                "status": s.status,
            }
            for s in steps
        ]
