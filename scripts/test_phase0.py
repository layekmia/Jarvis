"""
Phase 0 Sanity Check Script — Manual verification for backend.

Run this script to verify:
  1. Python venv is active
  2. All required packages are importable
  3. .env file loads correctly with valid API key
  4. Backend HTTP health endpoint responds
  5. WebSocket ping-pong works

Usage:
  backend\\.venv\\Scripts\\python.exe scripts\\test_phase0.py
"""

import sys
import json
import asyncio
from pathlib import Path

# Add project root to path so 'backend' package is importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_imports() -> bool:
    """Check all required packages are installed."""
    print("\n[1/5] Checking required packages...")
    required = ["fastapi", "uvicorn", "websockets", "dotenv", "openai",
                "pydantic", "httpx", "loguru", "pydantic_settings"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} — MISSING!")
            missing.append(pkg)
    if missing:
        print(f"\n  ⚠️  Missing packages: {missing}")
        print(f"  Run: backend\\.venv\\Scripts\\pip.exe install -r backend\\requirements.txt")
        return False
    return True


def check_config() -> bool:
    """Check .env loads and API key is valid format."""
    print("\n[2/5] Checking configuration...")
    try:
        from backend.core.config import settings
        key_preview = settings.openai_api_key[:8] + "..." + settings.openai_api_key[-4:]
        print(f"  ✅ OPENAI_API_KEY loaded: {key_preview}")
        print(f"  ✅ Backend: {settings.backend_host}:{settings.backend_port}")
        print(f"  ✅ Model (default): {settings.model_reasoning_default}")
        print(f"  ✅ Model (complex): {settings.model_reasoning_complex}")
        return True
    except SystemExit:
        print("  ❌ Configuration failed! Check your .env file.")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


def check_env_file() -> bool:
    """Verify .env file exists and has required key."""
    print("\n[3/5] Checking .env file...")
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        print(f"  ❌ .env file NOT FOUND at {env_path}")
        return False
    content = env_path.read_text()
    if "OPENAI_API_KEY" not in content:
        print("  ❌ OPENAI_API_KEY not found in .env file!")
        return False
    print(f"  ✅ .env file exists at {env_path}")
    print("  ✅ OPENAI_API_KEY present in .env")
    # Check gitignore
    gitignore_path = PROJECT_ROOT / ".gitignore"
    if gitignore_path.exists():
        if ".env" in gitignore_path.read_text():
            print("  ✅ .env is in .gitignore (safe!)")
        else:
            print("  ⚠️  .env is NOT in .gitignore — API key could be leaked!")
    return True


async def check_backend_http() -> bool:
    """Check HTTP health endpoint (requires backend to be running)."""
    print("\n[4/5] Checking backend HTTP health endpoint...")
    try:
        import httpx
        from backend.core.config import settings
        url = f"http://{settings.backend_host}:{settings.backend_port}/health"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                print(f"  ✅ GET /health → 200 OK")
                print(f"  ✅ Status: {data.get('status')}")
                print(f"  ✅ Version: {data.get('version')}")
                return True
            else:
                print(f"  ❌ GET /health → HTTP {resp.status_code}")
                return False
    except Exception as e:
        print(f"  ⚠️  Could not reach backend")
        print(f"  ℹ️  Make sure backend is running: scripts\\start_backend.bat")
        print(f"  Error: {e}")
        return False


async def check_websocket_pingpong() -> bool:
    """Test WebSocket ping-pong."""
    print("\n[5/5] Testing WebSocket ping-pong...")
    try:
        import websockets
        from backend.core.config import settings
        uri = f"ws://{settings.backend_host}:{settings.backend_port}/ws"

        async with websockets.connect(uri, open_timeout=5) as ws:
            # First message should be 'connected'
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
            msg = json.loads(raw)
            if msg.get("type") == "connected":
                print(f"  ✅ Received 'connected' event from backend!")
            else:
                print(f"  ⚠️  Expected 'connected' but got: {msg.get('type')}")

            # Send ping
            await ws.send(json.dumps({"type": "ping", "payload": {"message": "hello jarvis"}}))
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
            msg = json.loads(raw)
            if msg.get("type") == "pong":
                echo = msg.get("payload", {}).get("echo", "")
                print(f"  ✅ Ping → Pong! Echo: '{echo}'")
                return True
            else:
                print(f"  ❌ Expected 'pong' but got: {msg.get('type')}")
                return False

    except Exception as e:
        print(f"  ⚠️  WebSocket test failed (is backend running?)")
        print(f"  Error: {e}")
        return False


async def main() -> None:
    print("=" * 60)
    print("  JARVIS Phase 0 — Sanity Check")
    print("=" * 60)

    results = {
        "imports": check_imports(),
        "env_file": check_env_file(),
        "config": check_config(),
        "http": await check_backend_http(),
        "websocket": await check_websocket_pingpong(),
    }

    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {check}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("  🎉 ALL CHECKS PASSED! Phase 0 is complete.")
    else:
        print("  ⚠️  Some checks failed. See details above.")
        print("  Make sure the backend is running before tests 4 & 5.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
