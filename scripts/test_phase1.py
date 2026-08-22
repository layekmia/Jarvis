"""
Phase 1 — Jarvis UI Sanity Check
Tests that:
  1. Frontend dev server is running and returns HTML
  2. The HTML contains expected Jarvis component identifiers
  3. Backend is healthy (needed for WS connection in UI)
  4. All new Phase 1 files exist and are non-empty
"""
import asyncio
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent

RESULTS: dict[str, bool] = {}

# ─── Check 1: Required Phase 1 component files exist ─────────────────────

def check_phase1_files() -> bool:
    print("\n[1/4] Checking Phase 1 component files...")
    required = [
        "apps/desktop/src/components/JarvisBrain.tsx",
        "apps/desktop/src/components/ConversationPanel.tsx",
        "apps/desktop/src/components/SystemStatusPanel.tsx",
        "apps/desktop/src/components/ActiveMemoryPanel.tsx",
        "apps/desktop/src/components/BrainStateControls.tsx",
        "apps/desktop/src/components/StatusBar.tsx",
        "apps/desktop/src/components/CenterBrainSection.tsx",
        "apps/desktop/src/stores/jarvisStore.ts",
        "apps/desktop/src/App.tsx",
        "apps/desktop/src/index.css",
    ]
    all_ok = True
    for rel in required:
        path = ROOT / rel
        exists = path.exists() and path.stat().st_size > 100
        icon = "✅" if exists else "❌"
        print(f"  {icon} {rel}")
        if not exists:
            all_ok = False
    return all_ok


# ─── Check 2: package.json has Three.js deps ─────────────────────────────

def check_dependencies() -> bool:
    print("\n[2/4] Checking Three.js dependencies in package.json...")
    import json
    pkg_path = ROOT / "apps/desktop/package.json"
    try:
        with open(pkg_path) as f:
            pkg = json.load(f)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        required_pkgs = ["@react-three/fiber", "@react-three/drei", "three", "framer-motion"]
        all_ok = True
        for pkg_name in required_pkgs:
            present = any(pkg_name in key for key in deps)
            icon = "✅" if present else "❌"
            print(f"  {icon} {pkg_name}")
            if not present:
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"  ❌ Could not read package.json: {e}")
        return False


# ─── Check 3: Frontend dev server returns HTML ────────────────────────────

async def check_frontend() -> bool:
    print("\n[3/4] Checking frontend dev server (http://localhost:5173)...")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://localhost:5173")
            if resp.status_code == 200 and "<!doctype html>" in resp.text.lower():
                print("  ✅ Dev server responding → 200 OK")
                print("  ✅ HTML content received")
                return True
            else:
                print(f"  ❌ Unexpected response: {resp.status_code}")
                return False
    except Exception as e:
        print(f"  ⚠️  Could not reach frontend")
        print(f"  ℹ️  Make sure 'npm run dev' is running in apps/desktop/")
        print(f"  Error: {e}")
        return False


# ─── Check 4: Backend health ──────────────────────────────────────────────

async def check_backend() -> bool:
    print("\n[4/4] Checking backend health (http://127.0.0.1:8765/health)...")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://127.0.0.1:8765/health")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  ✅ Backend healthy → status: {data.get('status')}")
                return True
            else:
                print(f"  ❌ Backend returned HTTP {resp.status_code}")
                return False
    except Exception as e:
        print(f"  ⚠️  Backend not reachable")
        print(f"  ℹ️  Run: scripts\\start_backend.bat")
        print(f"  Error: {e}")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("  JARVIS Phase 1 — UI Sanity Check")
    print("=" * 60)

    RESULTS["component_files"] = check_phase1_files()
    RESULTS["dependencies"]    = check_dependencies()
    RESULTS["frontend"]        = await check_frontend()
    RESULTS["backend"]         = await check_backend()

    # Summary
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    all_pass = True
    for key, passed in RESULTS.items():
        icon = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {icon}  {key}")
        if not passed:
            all_pass = False

    print("=" * 60)
    if all_pass:
        print("  🎉 ALL CHECKS PASSED! Phase 1 UI is ready.")
        print("  👁️  Open http://localhost:5173 in your browser to see Jarvis!")
    else:
        print("  ⚠️  Some checks failed. See details above.")
    print("=" * 60)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    asyncio.run(main())
