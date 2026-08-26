"""
Phase 6 — Browser Automation Tools (Playwright Async API)

Uses the async Playwright API to remain fully compatible with FastAPI's
asyncio event loop. All tool functions are native coroutines (async def)
and must be awaited by the caller (planner.py).

Maintains a singleton async browser instance so consecutive commands
(open_url -> search_web -> fill_form) operate on the same window.
"""

from typing import Optional
from loguru import logger
from playwright.async_api import (
    async_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
)


class AsyncBrowserManager:
    """Async singleton to manage Playwright browser lifecycle."""
    _instance: Optional["AsyncBrowserManager"] = None

    def __new__(cls) -> "AsyncBrowserManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._playwright: Optional[Playwright] = None
            cls._instance._browser: Optional[Browser] = None
            cls._instance._context: Optional[BrowserContext] = None
            cls._instance._page: Optional[Page] = None
        return cls._instance

    async def get_page(self) -> Page:
        """Returns the active page, initializing the browser if necessary."""
        if self._playwright is None:
            logger.info("Initializing Playwright (async)...")
            self._playwright = await async_playwright().start()

        if self._browser is None or not self._browser.is_connected():
            logger.info("Launching Chromium browser (headed)...")
            self._browser = await self._playwright.chromium.launch(
                headless=False,
                args=["--start-maximized"],
            )

        if self._context is None:
            self._context = await self._browser.new_context(no_viewport=True)

        if self._page is None or self._page.is_closed():
            self._page = await self._context.new_page()

        return self._page

    async def close(self) -> None:
        """Closes the browser and Playwright cleanly."""
        try:
            if self._context:
                await self._context.close()
                self._context = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            self._page = None
            logger.info("Playwright browser closed.")
        except Exception as e:
            logger.warning(f"Error while closing browser: {e}")


browser_manager = AsyncBrowserManager()


# ── Tool Functions (all async) ────────────────────────────────────────────────

async def open_url(url: str) -> str:
    """Opens a specified URL in the browser."""
    if not url.startswith("http"):
        url = "https://" + url

    try:
        page = await browser_manager.get_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        title = await page.title()
        logger.success(f"Opened URL: {url} (Title: {title})")
        return f"Successfully opened {url}. Page title is '{title}'."
    except Exception as e:
        logger.error(f"Failed to open URL {url}: {e}")
        return f"Failed to open {url}. Error: {str(e)}"


async def search_web(query: str) -> str:
    """Searches Google for the given query."""
    try:
        page = await browser_manager.get_page()
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
    """Searches YouTube for the given query."""
    try:
        page = await browser_manager.get_page()
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
    """Fills an input field on the current page with a value."""
    try:
        page = await browser_manager.get_page()
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
    """Switches to the browser tab at the given index (0-based)."""
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
    """Closes the Playwright browser."""
    try:
        await browser_manager.close()
        return "Successfully closed the browser."
    except Exception as e:
        return f"Failed to close browser: {str(e)}"
