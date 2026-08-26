"""
Phase 5 — File System Tools: Sanity Check

Tests all Phase 5 file tools directly (no AI/API calls needed):
  - search_file
  - create_file
  - read_file_summary
  - copy_file
  - list_directory
  - rename_file / rename_file_confirmed
  - move_file / move_file_confirmed
  - delete_file / delete_file_confirmed
  - Safety: path outside home dir should be blocked
  - Confirmation sentinel: destructive ops return CONFIRM_NEEDED

Run:
    $env:PYTHONIOENCODING="utf-8"; backend\\.venv\\Scripts\\python.exe scripts\\test_phase5.py
"""

import sys
import os
import tempfile
import shutil
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
        ALLOWED_ROOTS,
    )
    ok("Imported all Phase 5 file tools successfully")
except ImportError as e:
    fail("Import failed", str(e))
    sys.exit(1)

# ── Setup: temp directory inside Downloads (inside ALLOWED_ROOTS) ──────────────
section("Setup")
TEST_DIR = Path.home() / "Downloads" / "_jarvis_phase5_test"
try:
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    ok(f"Created temp test directory: {TEST_DIR}")
except Exception as e:
    fail("Could not create test directory", str(e))
    sys.exit(1)

# ── Test: create_file ──────────────────────────────────────────────────────────
section("create_file")

test_file = str(TEST_DIR / "hello.txt")
result = create_file(test_file, content="Hello from Jarvis Phase 5!")
if "successfully" in result.lower():
    ok(f"create_file: {result}")
else:
    fail("create_file returned unexpected result", result)

# Creating same file again should fail gracefully
result2 = create_file(test_file)
if "already exists" in result2.lower():
    ok("create_file duplicate: correctly blocked duplicate creation")
else:
    fail("create_file duplicate: should have reported existing file", result2)

# ── Test: read_file_summary ────────────────────────────────────────────────────
section("read_file_summary")

result = read_file_summary(test_file)
if "Hello from Jarvis" in result and "hello.txt" in result:
    ok("read_file_summary: content and filename present")
else:
    fail("read_file_summary: missing expected content", result)

# Non-existent file
result = read_file_summary(str(TEST_DIR / "no_such_file.txt"))
if "not found" in result.lower():
    ok("read_file_summary missing file: correctly reported not found")
else:
    fail("read_file_summary missing file: wrong error", result)

# ── Test: search_file ─────────────────────────────────────────────────────────
section("search_file")

# Search by exact name
result = search_file("hello.txt", search_in=str(TEST_DIR))
if "hello.txt" in result:
    ok("search_file exact name: found file")
else:
    fail("search_file exact name: file not found", result)

# Glob pattern
result = search_file("*.txt", search_in=str(TEST_DIR))
if "hello.txt" in result:
    ok("search_file glob *.txt: found file")
else:
    fail("search_file glob *.txt: file not found", result)

# Search for non-existent
result = search_file("nonexistent_xyz_abc.txt", search_in=str(TEST_DIR))
if "no files" in result.lower():
    ok("search_file not found: correctly reported no match")
else:
    fail("search_file not found: wrong message", result)

# ── Test: list_directory ───────────────────────────────────────────────────────
section("list_directory")

result = list_directory(str(TEST_DIR))
if "hello.txt" in result:
    ok("list_directory: found file in listing")
else:
    fail("list_directory: file not in listing", result)

# Non-existent dir
result = list_directory(str(TEST_DIR / "no_such_dir"))
if "not found" in result.lower():
    ok("list_directory missing: correctly reported not found")
else:
    fail("list_directory missing: wrong message", result)

# ── Test: copy_file ────────────────────────────────────────────────────────────
section("copy_file")

copy_dest = str(TEST_DIR / "hello_copy.txt")
result = copy_file(test_file, copy_dest)
if "successfully" in result.lower() and Path(copy_dest).exists():
    ok("copy_file: file copied and exists on disk")
else:
    fail("copy_file: copy not successful", result)

# ── Test: rename_file (confirmation sentinel) ──────────────────────────────────
section("rename_file — confirmation sentinel")

result = rename_file(copy_dest, "hello_renamed.txt")
if result.startswith(CONFIRM_PREFIX):
    ok(f"rename_file: returned CONFIRM_NEEDED sentinel")
else:
    fail("rename_file: should have returned confirmation sentinel", result)

# Confirmed rename
result2 = rename_file_confirmed(copy_dest, "hello_renamed.txt")
renamed_path = TEST_DIR / "hello_renamed.txt"
if "successfully" in result2.lower() and renamed_path.exists():
    ok("rename_file_confirmed: file renamed and exists on disk")
else:
    fail("rename_file_confirmed: unexpected result", result2)

# ── Test: move_file (confirmation sentinel) ────────────────────────────────────
section("move_file — confirmation sentinel")

move_dest_dir = TEST_DIR / "subdir"
move_dest_dir.mkdir(exist_ok=True)
move_dest = str(move_dest_dir / "hello_moved.txt")

result = move_file(str(renamed_path), move_dest)
if result.startswith(CONFIRM_PREFIX):
    ok("move_file: returned CONFIRM_NEEDED sentinel")
else:
    fail("move_file: should have returned confirmation sentinel", result)

# Confirmed move
result2 = move_file_confirmed(str(renamed_path), move_dest)
if "successfully" in result2.lower() and Path(move_dest).exists():
    ok("move_file_confirmed: file moved and exists at destination")
else:
    fail("move_file_confirmed: unexpected result", result2)

# ── Test: delete_file (confirmation sentinel) ──────────────────────────────────
section("delete_file — confirmation sentinel")

result = delete_file(move_dest)
if result.startswith(CONFIRM_PREFIX):
    ok("delete_file: returned CONFIRM_NEEDED sentinel (did NOT delete yet)")
else:
    fail("delete_file: should have returned confirmation sentinel", result)

# File must still exist since we haven't confirmed
if Path(move_dest).exists():
    ok("delete_file: file still exists (confirmation pending — correct)")
else:
    fail("delete_file: file was deleted without confirmation!")

# Confirmed delete
result2 = delete_file_confirmed(move_dest)
if "deleted" in result2.lower() and not Path(move_dest).exists():
    ok("delete_file_confirmed: file deleted from disk")
else:
    fail("delete_file_confirmed: unexpected result or file still present", result2)

# ── Test: Safety — block path outside home ─────────────────────────────────────
section("Safety — path outside ALLOWED_ROOTS")

unsafe_path = "C:\\Windows\\System32\\test_jarvis.txt"
result = create_file(unsafe_path)
if "not allowed" in result.lower():
    ok(f"Safety create_file: correctly blocked unsafe path")
else:
    fail("Safety create_file: should have blocked system path", result)

result = delete_file(unsafe_path)
if "not found" in result.lower() or "not allowed" in result.lower():
    ok("Safety delete_file: correctly blocked or reported not found")
else:
    fail("Safety delete_file: unexpected result for system path", result)

# ── Cleanup ────────────────────────────────────────────────────────────────────
section("Cleanup")
try:
    shutil.rmtree(TEST_DIR)
    ok(f"Removed test directory: {TEST_DIR}")
except Exception as e:
    fail("Could not clean up test directory", str(e))

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"\n{'═' * 60}")
total = passed + failed
print(f"  Results: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET} / {total} total")
print(f"{'═' * 60}\n")

if failed > 0:
    sys.exit(1)
else:
    print(f"{GREEN}  🎉 All Phase 5 tests passed!{RESET}\n")
    sys.exit(0)
