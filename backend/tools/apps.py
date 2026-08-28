import os
import json
import subprocess
import pygetwindow as gw
from loguru import logger
import psutil
from pathlib import Path

try:
    from rapidfuzz import fuzz as _fuzz, process as _fuzz_process
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False
    logger.warning("rapidfuzz not installed — fuzzy app search disabled. Run: pip install rapidfuzz")

# Aliases used for opening apps (can be executables, URIs, or URLs)
# Special sentinel values:
#   "__CHROME__"  -> handled by _open_chrome_with_profile()
#   "__EDGE__"    -> handled by _open_edge_with_profile()
OPEN_ALIASES = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "vs code": "code.exe",
    "vscode": "code.exe",
    "code": "code.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "whatsapp": "whatsapp:",
    "microsoft store": "ms-windows-store:",
    "store": "ms-windows-store:",
    "settings": "ms-settings:",
    "spotify": "spotify:",
    "netflix": "netflix:",
    # NOTE: Chrome, Edge, YouTube, Facebook, Google are intentionally NOT here.
    # Browser operations (open Chrome, open websites) are handled by the
    # open_browser / open_url tools in browser_tools.py via Playwright.
}

# Aliases used for closing apps (MUST be process names, usually ending in .exe)
CLOSE_ALIASES = {
    "notepad": "notepad.exe",
    "calculator": "CalculatorApp.exe",
    "calc": "CalculatorApp.exe",
    "vs code": "code.exe",
    "vscode": "code.exe",
    "code": "code.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "whatsapp": "WhatsApp.Root.exe",
    "microsoft store": "WinStore.App.exe",
    "store": "WinStore.App.exe",
    "settings": "SystemSettings.exe",
    "spotify": "Spotify.exe",
    "netflix": "Netflix.exe",
}

WEBSITES = {"youtube", "facebook", "google", "gmail"}

# ── Start Menu Scanner ─────────────────────────────────────────────────────────

# Cached list of (display_name, lnk_path) tuples from Start Menu shortcuts
_START_MENU_CACHE: list[tuple[str, str]] | None = None

_START_MENU_DIRS = [
    Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
]


def _get_start_menu_apps() -> list[tuple[str, str]]:
    """
    Scans Start Menu directories for .lnk shortcuts and returns a list of
    (app_display_name, shortcut_path) tuples. Results are cached for the
    process lifetime.
    """
    global _START_MENU_CACHE
    if _START_MENU_CACHE is not None:
        return _START_MENU_CACHE

    apps: list[tuple[str, str]] = []
    for start_dir in _START_MENU_DIRS:
        if not start_dir.exists():
            continue
        try:
            for lnk in start_dir.rglob("*.lnk"):
                # Use stem as the display name (e.g. "Antispace Gravity" from "Antispace Gravity.lnk")
                apps.append((lnk.stem, str(lnk)))
        except PermissionError:
            pass

    _START_MENU_CACHE = apps
    logger.debug(f"Start Menu scan: found {len(apps)} shortcuts")
    return apps


def _normalize_app_name(name: str) -> str:
    """Lowercase and strip common filler words for better fuzzy comparison."""
    import re
    name = name.lower()
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _fuzzy_find_app(query: str, candidates: dict[str, str], threshold: int = 65) -> str | None:
    """
    Uses rapidfuzz to find the best matching key in `candidates`.
    Returns the corresponding value (executable/path), or None if no match.
    """
    if not _RAPIDFUZZ_AVAILABLE or not candidates:
        return None

    query_norm = _normalize_app_name(query)
    keys = list(candidates.keys())
    norm_keys = [_normalize_app_name(k) for k in keys]

    result = _fuzz_process.extractOne(
        query_norm,
        norm_keys,
        scorer=_fuzz.partial_ratio,
        score_cutoff=threshold,
    )
    if result is None:
        return None

    best_norm, score, idx = result
    matched_key = keys[idx]
    logger.info(f"Fuzzy alias match: '{query}' → '{matched_key}' (score: {score}%)")
    return candidates[matched_key]


def _fuzzy_find_start_menu(query: str, threshold: int = 65) -> str | None:
    """
    Searches Start Menu shortcuts with fuzzy matching.
    Returns the .lnk path of the best match, or None.
    """
    if not _RAPIDFUZZ_AVAILABLE:
        return None

    apps = _get_start_menu_apps()
    if not apps:
        return None

    query_norm = _normalize_app_name(query)
    names = [a[0] for a in apps]
    norm_names = [_normalize_app_name(n) for n in names]

    result = _fuzz_process.extractOne(
        query_norm,
        norm_names,
        scorer=_fuzz.partial_ratio,
        score_cutoff=threshold,
    )
    if result is None:
        return None

    best_norm, score, idx = result
    matched_name, lnk_path = apps[idx]
    logger.info(f"Fuzzy Start Menu match: '{query}' → '{matched_name}' (score: {score}%)")
    return lnk_path


# ── Browser Profile Helpers ────────────────────────────────────────────────────

_CHROME_USER_DATA = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
_EDGE_USER_DATA   = Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data"

# Common Chrome/Edge executable locations
_CHROME_EXE_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
]
_EDGE_EXE_PATHS = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def _find_exe(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def _get_browser_profiles(user_data: Path) -> dict[str, str]:
    """
    Reads browser Local State file and returns a dict of
    {display_name_lower: profile_directory} e.g. {"layek miah": "Default"}.
    """
    local_state = user_data / "Local State"
    if not local_state.exists():
        return {}
    try:
        data = json.loads(local_state.read_text(encoding="utf-8"))
        info_cache = data.get("profile", {}).get("info_cache", {})
        profiles: dict[str, str] = {}
        for dir_name, info in info_cache.items():
            # Use display name and google account name as lookup keys
            for key in [info.get("name", ""), info.get("gaia_name", ""), info.get("shortcut_name", "")]:
                if key:
                    profiles[key.lower()] = dir_name
        return profiles
    except Exception as e:
        logger.warning(f"Could not read browser profiles: {e}")
        return {}


def _get_last_used_profile(user_data: Path) -> str:
    """Returns the last-used profile directory name (e.g. 'Default')."""
    local_state = user_data / "Local State"
    if not local_state.exists():
        return "Default"
    try:
        data = json.loads(local_state.read_text(encoding="utf-8"))
        return data.get("profile", {}).get("last_used", "Default")
    except Exception:
        return "Default"


def _fuzzy_find_profile(query: str, profiles: dict[str, str]) -> str | None:
    """Fuzzy-match a user's spoken profile name against known profile display names."""
    if not profiles or not _RAPIDFUZZ_AVAILABLE:
        return None
    keys = list(profiles.keys())
    result = _fuzz_process.extractOne(
        query.lower(), keys, scorer=_fuzz.partial_ratio, score_cutoff=60
    )
    if result:
        matched_key, score, _ = result
        logger.info(f"Profile fuzzy match: '{query}' → '{matched_key}' (score: {score}%)")
        return profiles[matched_key]
    return None


def _open_browser_with_profile(
    exe_paths: list[Path],
    user_data: Path,
    browser_name: str,
    profile_hint: str | None = None,
) -> str:
    """
    Launches a Chromium-based browser with the correct --profile-directory flag.

    Profile resolution:
      1. If profile_hint given → fuzzy match against known profile names
      2. Otherwise → always use "Default" (the user's own primary profile)
    """
    exe = _find_exe(exe_paths)
    if exe is None:
        # Fallback: let Windows resolve via PATH
        exe_name = "chrome.exe" if "Chrome" in browser_name else "msedge.exe"
        logger.warning(f"{browser_name} exe not found in known paths, trying PATH fallback")
        exe = Path(exe_name)

    profiles = _get_browser_profiles(user_data)

    # Determine which profile directory to use
    profile_dir: str | None = None
    if profile_hint:
        profile_dir = _fuzzy_find_profile(profile_hint, profiles)
        if profile_dir:
            logger.info(f"Opening {browser_name} with requested profile: {profile_dir}")
        else:
            logger.warning(f"Profile hint '{profile_hint}' not matched — falling back to Default")

    if profile_dir is None:
        # Always open the user's own Default profile unless explicitly told otherwise
        profile_dir = "Default"
        logger.info(f"Opening {browser_name} with Default profile")

    cmd = [
        str(exe),
        f"--profile-directory={profile_dir}",
    ]
    try:
        subprocess.Popen(cmd)
        # Find display name for the profile directory
        display = next((k.title() for k, v in profiles.items() if v == profile_dir), profile_dir)
        logger.success(f"Launched {browser_name} with profile '{display}' ({profile_dir})")
        return f"Opened {browser_name} with profile: {display}."
    except Exception as e:
        logger.error(f"Failed to launch {browser_name}: {e}")
        return f"Failed to open {browser_name}: {str(e)}"


def _open_chrome_with_profile(profile_hint: str | None = None) -> str:
    return _open_browser_with_profile(_CHROME_EXE_PATHS, _CHROME_USER_DATA, "Chrome", profile_hint)


def _open_edge_with_profile(profile_hint: str | None = None) -> str:
    return _open_browser_with_profile(_EDGE_EXE_PATHS, _EDGE_USER_DATA, "Edge", profile_hint)


# ── Tool Functions ─────────────────────────────────────────────────────────────

def open_app(name: str, profile: str | None = None, new_window: bool = False) -> str:
    """
    Opens an application by name on Windows.

    Args:
        name:    App name (e.g. "chrome", "notepad", "Antigravity IDE")
        profile: Optional browser profile name for Chrome/Edge
                 (e.g. "Layek", "Rasel"). If omitted, uses last-used profile.
        new_window: If True, skips checking if the app is already open and forces a new instance.

    Resolution order:
      1. Exact alias match (OPEN_ALIASES dict)
      2. Fuzzy alias match (rapidfuzz against OPEN_ALIASES keys, threshold 65%)
      3. Fuzzy Start Menu shortcut match (rapidfuzz against .lnk stems, threshold 65%)
      4. Direct execution attempt (pass name as-is to the 'start' command)
    """
    name_lower = name.lower().strip()

    # Check if it's already running (only if new_window is False)
    if not new_window:
        executable_to_check = CLOSE_ALIASES.get(name_lower, name_lower)
        if not executable_to_check.endswith(".exe"):
            executable_to_check += ".exe"
            
        is_running = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == executable_to_check:
                    is_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if is_running:
            return f"Boss, {name.title()} is already open. (If you want another window, please say 'open a new {name} window')."

    # 1. Exact alias match
    executable = OPEN_ALIASES.get(name_lower)

    # 2. Fuzzy alias match
    if executable is None and _RAPIDFUZZ_AVAILABLE:
        executable = _fuzzy_find_app(name_lower, OPEN_ALIASES)

    # ── Browser sentinel handling ──────────────────────────────────────────
    if executable == "__CHROME__":
        return _open_chrome_with_profile(profile)
    if executable == "__EDGE__":
        return _open_edge_with_profile(profile)

    # If user is asking for chrome/edge with a profile hint but matched via fuzzy
    # and executable resolved to a sentinel via fuzzy, handle that too.
    # (Covered above already since fuzzy returns the alias value.)

    # 3. Fuzzy Start Menu match
    lnk_path: str | None = None
    if executable is None:
        lnk_path = _fuzzy_find_start_menu(name_lower)

    try:
        if lnk_path:
            # Launch via the .lnk shortcut
            subprocess.Popen(f'start "" "{lnk_path}"', shell=True)
            matched_name = Path(lnk_path).stem
            logger.success(f"Opened Start Menu app: {matched_name} ({lnk_path})")
            return f"Successfully opened {matched_name}."
        else:
            # Use resolved executable (or raw name as last resort)
            target = executable if executable is not None else name_lower
            subprocess.Popen(f'start "" "{target}"', shell=True)
            logger.success(f"Opened application: {target}")
            return f"Successfully opened {name}."
    except Exception as e:
        logger.error(f"Failed to open application '{name}': {e}")
        return f"Failed to open {name}. Error: {str(e)}"


def close_app(name: str) -> str:
    """Closes an application gracefully using psutil."""
    name_lower = name.lower().strip()
    
    if name_lower in WEBSITES:
        return f"{name} is a website running in your browser. Please use 'close_browser' to close it, or close the browser tab manually."
        
    executable = CLOSE_ALIASES.get(name_lower, name_lower)
    
    # Ensure it ends with .exe for matching process names
    if not executable.endswith(".exe"):
        executable += ".exe"
        
    closed_count = 0
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == executable:
                    proc.terminate()
                    closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if closed_count > 0:
            logger.success(f"Closed {closed_count} instances of {executable}")
            return f"Successfully closed {name}."
        else:
            # Fallback to taskkill
            result = subprocess.run(f"taskkill /F /IM {executable}", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.success(f"Closed {executable} using taskkill")
                return f"Successfully closed {name}."
            else:
                logger.warning(f"Could not find any running process for {name}")
                return f"Could not find any running application named {name} to close."
    except Exception as e:
        logger.error(f"Error closing {name}: {e}")
        return f"An error occurred while trying to close {name}."

def switch_app(name: str) -> str:
    """Brings an application window to the foreground."""
    try:
        # Search for windows containing the name
        windows = gw.getWindowsWithTitle(name)
        if not windows:
            return f"Could not find any open window containing the name '{name}'."
            
        # Try to focus the first match
        win = windows[0]
        
        # If window is minimized, restore it
        if win.isMinimized:
            win.restore()
            
        try:
            import ctypes
            # Workaround for Windows focus stealing prevention
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0) # ALT down
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0) # ALT up
            win.activate()
        except Exception as act_e:
            if "Error code from Windows: 0" not in str(act_e):
                raise act_e
            
        logger.success(f"Switched focus to window: {win.title}")
        return f"Switched focus to {name}."
    except Exception as e:
        logger.error(f"Failed to switch to {name}: {e}")
        return f"Failed to switch to {name}. It may require manual focus."
