"""
Phase 6 — Browser Automation Tools: Sanity Check

Tests the Playwright browser tools directly.
Run:
    $env:PYTHONIOENCODING="utf-8"; backend\.venv\Scripts\python.exe scripts\test_phase6.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

passed = 0
failed = 0

def ok(msg: str) -> None:
    global passed
    passed += 1
    print(f"{GREEN}  ✅ PASS{RESET} — {msg}")

def fail(msg: str, detail: str = "") -> None:
    global failed
    failed += 1
    print(f"{RED}  ❌ FAIL{RESET} — {msg}")
    if detail:
        print(f"       Detail: {detail}")

def section(title: str) -> None:
    print(f"\n{YELLOW}{'─' * 60}{RESET}")
    print(f"{YELLOW}  {title}{RESET}")
    print(f"{YELLOW}{'─' * 60}{RESET}")

# ── Import tools ───────────────────────────────────────────────────────────────
try:
    from backend.tools.browser.browser_tools import (
        open_url,
        search_web,
        youtube_search,
        switch_tab,
        close_browser
    )
    ok("Imported all Phase 6 browser tools successfully")
except ImportError as e:
    fail("Import failed", str(e))
    sys.exit(1)

# ── Test: open_url ─────────────────────────────────────────────────────────────
section("open_url")
print("This should open a browser window and go to example.com...")
result = open_url("example.com")
if "Successfully opened" in result:
    ok(f"open_url: {result}")
else:
    fail("open_url returned unexpected result", result)

time.sleep(2)

# ── Test: search_web ───────────────────────────────────────────────────────────
section("search_web")
print("This should navigate to Google and search for 'OpenAI'...")
result = search_web("OpenAI")
if "Successfully searched" in result:
    ok(f"search_web: {result}")
else:
    fail("search_web returned unexpected result", result)

time.sleep(2)

# ── Test: youtube_search ───────────────────────────────────────────────────────
section("youtube_search")
print("This should open a NEW tab (via playwright if we designed it that way... wait we didn't)")
print("It will just navigate the current tab to YouTube.")
result = youtube_search("Rick Astley Never Gonna Give You Up")
if "Successfully searched" in result:
    ok(f"youtube_search: {result}")
else:
    fail("youtube_search returned unexpected result", result)

time.sleep(2)

# ── Test: switch_tab ───────────────────────────────────────────────────────────
section("switch_tab")
# We only have 1 tab right now because we reused it. Let's try switching to index 0
result = switch_tab(0)
if "Switched to tab" in result:
    ok(f"switch_tab: {result}")
else:
    fail("switch_tab failed", result)

# ── Cleanup ────────────────────────────────────────────────────────────────────
section("Cleanup")
print("Closing browser...")
result = close_browser()
if "Successfully closed" in result:
    ok("Browser closed.")
else:
    fail("close_browser failed", result)

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"\n{'═' * 60}")
total = passed + failed
print(f"  Results: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET} / {total} total")
print(f"{'═' * 60}\n")

if failed > 0:
    sys.exit(1)
else:
    print(f"{GREEN}  🎉 All Phase 6 tests passed!{RESET}\n")
    sys.exit(0)
