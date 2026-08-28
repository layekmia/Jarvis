"""
Phase 6 — Browser Automation Tools (Playwright Async API)

Uses the async Playwright API to remain fully compatible with FastAPI's
asyncio event loop. All tool functions are native coroutines (async def)
and must be awaited by the caller (planner.py).

Singleton browser — real Chrome profile
----------------------------------------
Uses ``launch_persistent_context()`` with ``channel="chrome"`` so Jarvis
opens the user's actual installed Chrome with their Default profile
(bookmarks, cookies, logins — everything).

If Chrome is not installed or the profile is locked (Chrome already open
with the same profile), it falls back to Playwright's bundled Chromium
with a fresh session.

Crash / manual-close recovery
------------------------------
Before every operation, ``get_page()`` checks whether the context and page
are still healthy. If the user manually closes Chrome, the next command
transparently relaunches it.
"""

import json
from pathlib import Path
from typing import Optional
from loguru import logger
from playwright.async_api import (
    async_playwright,
    Playwright,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
)

# ── Chrome profile resolution ─────────────────────────────────────────────────

_CHROME_USER_DATA = (
    Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
)


def _get_last_used_profile() -> str:
    """Read Chrome's Local State to find the last-used profile directory."""
    local_state = _CHROME_USER_DATA / "Local State"
    try:
        data = json.loads(local_state.read_text(encoding="utf-8"))
        return data.get("profile", {}).get("last_used", "Default")
    except Exception:
        return "Default"


def _chrome_profile_dir() -> Path:
    """Return the absolute path to the Chrome profile directory to use."""
    profile_name = _get_last_used_profile()
    return _CHROME_USER_DATA / profile_name


# ── Manager ───────────────────────────────────────────────────────────────────

class AsyncBrowserManager:
    """
    Async singleton — manages a single persistent Playwright browser context
    that uses the user's real Chrome profile.
    """

    _instance: Optional["AsyncBrowserManager"] = None

    def __new__(cls) -> "AsyncBrowserManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._playwright: Optional[Playwright] = None
            cls._instance._context: Optional[BrowserContext] = None
            cls._instance._page: Optional[Page] = None
            cls._instance._using_fallback: bool = False
        return cls._instance

    # ── Health helpers ────────────────────────────────────────────────────────

    def _context_alive(self) -> bool:
        try:
            # A closed context raises on .pages access
            _ = self._context.pages
            return True
        except Exception:
            return False

    def _page_alive(self) -> bool:
        try:
            return self._page is not None and not self._page.is_closed()
        except Exception:
            return False

    # ── Launch ────────────────────────────────────────────────────────────────

    async def _launch(self) -> None:
        """
        Launch a persistent Chrome context with the user's real profile.
        Falls back to bundled Chromium if Chrome is unavailable or profile locked.
        """
        profile_dir = _chrome_profile_dir()
        logger.info(f"Launching Chrome with profile: {profile_dir}")

        try:
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                channel="chrome",          # Use the installed Chrome binary
                headless=False,
                args=[
                    "--start-maximized",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-extensions-except",  # keep user extensions
                ],
                no_viewport=True,
            )
            self._using_fallback = False
            logger.success("Launched Chrome with real user profile.")
        except Exception as e:
            logger.warning(
                f"Could not launch Chrome with real profile ({e}). "
                "Falling back to bundled Chromium..."
            )
            # Fallback: bundled Playwright Chromium (guest session)
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(Path.home() / ".jarvis_browser_profile"),
                headless=False,
                args=["--start-maximized", "--no-first-run"],
                no_viewport=True,
            )
            self._using_fallback = True
            logger.info("Launched fallback Chromium browser.")

        self._page = None

    # ── Core lifecycle ────────────────────────────────────────────────────────

    async def get_page(self) -> Page:
        """
        Return a healthy, ready-to-use Page.

        1. Start Playwright if not yet started.
        2. If the context was closed (Chrome quit), relaunch.
        3. If the active tab was closed, reuse an existing tab or open a new one.
        """
        # 1. Playwright process
        if self._playwright is None:
            logger.info("Initializing Playwright...")
            self._playwright = await async_playwright().start()

        # 2. Context health — relaunch if Chrome was closed
        if self._context is None or not self._context_alive():
            if self._context is not None:
                logger.info("Browser was closed. Relaunching...")
            await self._launch()

        # 3. Page / tab
        if not self._page_alive():
            try:
                existing = self._context.pages
                # Filter out chrome:// and blank internal pages if real pages exist
                real_pages = [p for p in existing if not p.url.startswith("chrome://")]
                if real_pages:
                    self._page = real_pages[-1]
                    logger.info(f"Reusing tab: {self._page.url}")
                elif existing:
                    self._page = existing[-1]
                    logger.info(f"Reusing internal tab: {self._page.url}")
                else:
                    self._page = await self._context.new_page()
                    logger.info("Opened new tab.")
            except Exception:
                self._page = await self._context.new_page()
                logger.info("Opened new tab (fallback).")

        return self._page

    async def new_tab(self) -> Page:
        """Open a brand-new tab and make it the active page."""
        await self.get_page()  # ensure context is alive
        self._page = await self._context.new_page()
        logger.info("Opened new tab.")
        return self._page

    async def close(self) -> None:
        """Close the browser context and Playwright cleanly."""
        try:
            if self._context:
                await self._context.close()
                self._context = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            self._page = None
            logger.info("Playwright browser closed.")
        except Exception as e:
            logger.warning(f"Error while closing browser: {e}")


browser_manager = AsyncBrowserManager()


# ── Internal helper ────────────────────────────────────────────────────────────

async def _safe_get_page() -> Page:
    """
    Wrapper around ``browser_manager.get_page()`` with one auto-retry on
    stale handle errors (e.g. context closed between calls).
    """
    try:
        return await browser_manager.get_page()
    except Exception as exc:
        logger.warning(f"get_page() failed ({exc}). Resetting and retrying...")
        browser_manager._context = None
        browser_manager._page = None
        return await browser_manager.get_page()



# ── Tool Functions (all async) ────────────────────────────────────────────────

async def open_browser(browser_name: str = "chrome") -> str:
    """
    Opens (or focuses) the Jarvis-managed browser window.
    Use this when the user says 'open chrome', 'browser kholo', 'open edge', etc.
    Does nothing extra if the browser is already open — just brings it to focus.
    """
    try:
        page = await _safe_get_page()
        await page.bring_to_front()
        logger.success("Browser window opened/focused.")
        return "Browser is open and ready, boss."
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
        return f"Could not open the browser. Error: {str(e)}"


async def open_url(url: str) -> str:
    """
    Opens a URL in the Jarvis-managed browser (same window, new tab if needed).
    Navigates the current tab. All subsequent browser ops use this same browser.
    """
    if not url.startswith("http"):
        url = "https://" + url

    try:
        page = await _safe_get_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        title = await page.title()
        logger.success(f"Navigated to: {url} (Title: {title})")
        return f"Opened {url} — page title: '{title}'."
    except Exception as e:
        logger.error(f"Failed to open URL {url}: {e}")
        return f"Failed to open {url}. Error: {str(e)}"


async def open_new_tab(url: str = "about:blank") -> str:
    """
    Opens a NEW tab in the same Jarvis-managed browser window and navigates to the URL.
    Use when user explicitly says 'new tab' or 'notun tab-e kholo'.
    """
    if url and url != "about:blank" and not url.startswith("http"):
        url = "https://" + url
    try:
        # Ensure context exists
        await _safe_get_page()
        new_page = await browser_manager._context.new_page()
        browser_manager._page = new_page
        if url and url != "about:blank":
            await new_page.goto(url, wait_until="domcontentloaded", timeout=20000)
            title = await new_page.title()
            logger.success(f"Opened new tab: {url} (Title: {title})")
            return f"Opened new tab with {url} — title: '{title}'."
        logger.success("Opened a new blank tab.")
        return "Opened a new tab, boss."
    except Exception as e:
        logger.error(f"Failed to open new tab: {e}")
        return f"Failed to open new tab. Error: {str(e)}"


async def search_web(query: str) -> str:
    """Search Google for the given query using the existing browser tab."""
    try:
        page = await _safe_get_page()
        await page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=15000)

        # Handle cookie consent if it appears
        try:
            accept_button = page.locator("button:has-text('Accept all')")
            if await accept_button.is_visible(timeout=2000):
                await accept_button.click()
        except Exception:
            pass

        search_box = page.locator("[name='q']")
        await search_box.fill(query)
        await search_box.press("Enter")
        await page.wait_for_load_state("domcontentloaded", timeout=10000)

        logger.success(f"Searched web for: {query}")
        return f"Successfully searched Google for '{query}'."
    except Exception as e:
        logger.error(f"Failed to search web for {query}: {e}")
        return f"Failed to search Google for '{query}'. Error: {str(e)}"


async def youtube_search(query: str) -> str:
    """Search YouTube for the given query using the existing browser tab."""
    try:
        page = await _safe_get_page()
        await page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=15000)

        # Handle cookie consent
        try:
            accept_button = page.locator("button:has-text('Accept all')")
            if await accept_button.is_visible(timeout=2000):
                await accept_button.click()
        except Exception:
            pass

        search_box = page.locator("[name='search_query']").first
        await search_box.fill(query)
        await search_box.press("Enter")
        await page.wait_for_load_state("domcontentloaded", timeout=10000)

        logger.success(f"Searched YouTube for: {query}")
        return f"Successfully searched YouTube for '{query}'."
    except Exception as e:
        logger.error(f"Failed to search YouTube for {query}: {e}")
        return f"Failed to search YouTube for '{query}'. Error: {str(e)}"


async def fill_form(selector: str, value: str) -> str:
    """Fill an input field on the current page with a value."""
    try:
        page = await _safe_get_page()
        element = page.locator(selector).first
        if not await element.is_visible(timeout=3000):
            return f"Element with selector '{selector}' not found or not visible."

        await element.fill(value)
        logger.success(f"Filled '{selector}' with '{value}'")
        return "Successfully filled the input field."
    except Exception as e:
        logger.error(f"Failed to fill form {selector}: {e}")
        return f"Failed to fill form. Error: {str(e)}"


async def switch_tab(index: int) -> str:
    """Switch to the browser tab at the given index (0-based)."""
    try:
        if not browser_manager._context:
            return "No browser window is currently open."

        pages = browser_manager._context.pages
        if not pages:
            return "No tabs are currently open."

        if index < 0 or index >= len(pages):
            return f"Invalid tab index {index}. There are only {len(pages)} open tabs."

        browser_manager._page = pages[index]
        await browser_manager._page.bring_to_front()
        title = await browser_manager._page.title()

        logger.success(f"Switched to tab {index} ({title})")
        return f"Switched to tab {index}. Page title is '{title}'."
    except Exception as e:
        logger.error(f"Failed to switch tab: {e}")
        return f"Failed to switch tab. Error: {str(e)}"


async def close_browser() -> str:
    """Close the Playwright browser."""
    try:
        await browser_manager.close()
        return "Successfully closed the browser."
    except Exception as e:
        return f"Failed to close browser: {str(e)}"
