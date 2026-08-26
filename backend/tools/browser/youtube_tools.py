"""
YouTube Play Tool
=================
Plays a song/video on YouTube by:
  1. Using yt-dlp to extract the first matching video URL (fast metadata-only lookup)
  2. Opening that direct video URL in Chrome with the user's preferred profile
  3. Fallback: if yt-dlp fails, opens the YouTube search results page instead

Also provides youtube_open() and an updated youtube_search() that both use
Chrome with the correct profile instead of an anonymous Playwright browser.
"""

import subprocess
from pathlib import Path
from urllib.parse import quote_plus
from loguru import logger

# ── Chrome Profile Configuration ──────────────────────────────────────────────
# This is the Chrome profile that has your YouTube account logged in.
# Rasel's profile = Profile 1
YOUTUBE_PROFILE_DIR: str = "Profile 1"

_CHROME_USER_DATA = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
_CHROME_EXE_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
]


def _get_chrome_exe() -> str:
    """Returns the path to the Chrome executable."""
    for p in _CHROME_EXE_PATHS:
        if p.exists():
            return str(p)
    return "chrome.exe"   # fallback: rely on PATH


def _open_url_in_chrome(url: str, profile_dir: str = YOUTUBE_PROFILE_DIR) -> None:
    """Launches Chrome with a specific profile and opens the given URL."""
    chrome = _get_chrome_exe()
    cmd = [chrome, f"--profile-directory={profile_dir}", url]
    subprocess.Popen(cmd)
    logger.info(f"Launched Chrome [{profile_dir}] → {url}")


# ── yt-dlp Video Lookup ────────────────────────────────────────────────────────

def _ytdlp_find_video_url(query: str) -> str | None:
    """
    Uses yt-dlp to find the first YouTube video URL matching the query.
    Only fetches metadata (no download). Returns the watch URL or None on failure.
    """
    try:
        import yt_dlp  # type: ignore

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",   # metadata only, no download
            "default_search": "ytsearch1",   # search YouTube, take first result
            "skip_download": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if info and "entries" in info and info["entries"]:
                entry = info["entries"][0]
                video_id = entry.get("id")
                title = entry.get("title", "Unknown")
                if video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    logger.success(f"yt-dlp found: '{title}' → {url}")
                    return url
    except Exception as e:
        logger.warning(f"yt-dlp lookup failed: {e}")
    return None


# ── Tool Functions ─────────────────────────────────────────────────────────────

def youtube_play(query: str) -> str:
    """
    Plays a song or video on YouTube in Chrome.

    Steps:
      1. Uses yt-dlp to find the first matching video URL.
      2. Opens that video directly in Chrome (with the YouTube profile).
      3. If yt-dlp fails, falls back to opening the search results page.

    Args:
        query: Song name, artist, or any YouTube search query.

    Returns:
        A success or error message.
    """
    logger.info(f"youtube_play: searching for '{query}'")

    # Step 1 — try yt-dlp direct video URL
    video_url = _ytdlp_find_video_url(query)

    if video_url:
        _open_url_in_chrome(video_url)
        return f"Playing '{query}' on YouTube."

    # Step 2 — fallback: YouTube search results page
    logger.warning("yt-dlp failed, falling back to YouTube search page")
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    _open_url_in_chrome(search_url)
    return (
        f"Couldn't find a direct link for '{query}', "
        f"so I've opened the YouTube search results for you."
    )


def youtube_open() -> str:
    """
    Opens YouTube homepage in Chrome with the user's YouTube profile.
    Used when the user says 'open YouTube' without a specific search query.

    Returns:
        A success message.
    """
    _open_url_in_chrome("https://www.youtube.com")
    logger.success("Opened YouTube homepage in Chrome.")
    return "Opened YouTube."


def youtube_search_chrome(query: str) -> str:
    """
    Searches YouTube for a query and opens the search results page in Chrome.
    Use this when the user wants to search/browse (not immediately play).

    Args:
        query: The search query.

    Returns:
        A success message.
    """
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    _open_url_in_chrome(search_url)
    logger.success(f"Opened YouTube search for '{query}' in Chrome.")
    return f"Opened YouTube search results for '{query}'."
