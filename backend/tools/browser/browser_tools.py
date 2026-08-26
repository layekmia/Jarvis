"""
Phase 6 — Browser Automation Tools (Playwright)

Maintains a singleton Playwright browser instance so that consecutive 
commands (e.g. open_url -> search_web -> fill_form) operate on the same window.
Uses the synchronous Playwright API (`playwright.sync_api`) since our TOOL_MAP
dispatcher expects synchronous functions.
"""

from typing import Optional
from loguru import logger
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout

class BrowserManager:
    """Singleton to manage Playwright browser lifecycle."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
            cls._instance._playwright: Optional[Playwright] = None
            cls._instance._browser: Optional[Browser] = None
            cls._instance._context: Optional[BrowserContext] = None
            cls._instance._page: Optional[Page] = None
        return cls._instance

    def get_page(self) -> Page:
        """Returns the active page, initializing the browser if necessary."""
        if not self._playwright:
            logger.info("Initializing Playwright...")
            self._playwright = sync_playwright().start()
            
        if not self._browser:
            logger.info("Launching Chromium browser...")
            # Headed mode so actions are visible to the user
            self._browser = self._playwright.chromium.launch(headless=False, args=["--start-maximized"])
            
        if not self._context:
            self._context = self._browser.new_context(no_viewport=True)
            
        if not self._page or self._page.is_closed():
            self._page = self._context.new_page()
            
        return self._page

    def close(self):
        """Closes the browser and Playwright."""
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        self._page = None
        logger.info("Playwright browser closed.")

browser_manager = BrowserManager()

# ── Tool Functions ─────────────────────────────────────────────────────────────

def open_url(url: str) -> str:
    """Opens a specified URL in the browser."""
    if not url.startswith("http"):
        url = "https://" + url
        
    try:
        page = browser_manager.get_page()
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        title = page.title()
        logger.success(f"Opened URL: {url} (Title: {title})")
        return f"Successfully opened {url}. Page title is '{title}'."
    except Exception as e:
        logger.error(f"Failed to open URL {url}: {e}")
        return f"Failed to open {url}. Error: {str(e)}"

def search_web(query: str) -> str:
    """Searches Google for the given query."""
    try:
        page = browser_manager.get_page()
        # Navigate to Google
        page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=15000)
        
        # Handle cookie consent if it appears (common in EU)
        try:
            accept_button = page.locator("button:has-text('Accept all')")
            if accept_button.is_visible(timeout=2000):
                accept_button.click()
        except Exception:
            pass

        # Fill search box and press enter
        search_box = page.locator("[name='q']")
        search_box.fill(query)
        search_box.press("Enter")
        
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        logger.success(f"Searched web for: {query}")
        return f"Successfully searched Google for '{query}'."
    except Exception as e:
        logger.error(f"Failed to search web for {query}: {e}")
        return f"Failed to search Google for '{query}'. Error: {str(e)}"

def youtube_search(query: str) -> str:
    """Searches YouTube for the given query and plays the first video if possible."""
    try:
        page = browser_manager.get_page()
        page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=15000)
        
        # Handle cookie consent
        try:
            accept_button = page.locator("button:has-text('Accept all')")
            if accept_button.is_visible(timeout=2000):
                accept_button.click()
        except Exception:
            pass

        # Fill search and press enter
        search_box = page.locator("[name='search_query']").first
        search_box.fill(query)
        search_box.press("Enter")
        
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        logger.success(f"Searched YouTube for: {query}")
        return f"Successfully searched YouTube for '{query}'."
    except Exception as e:
        logger.error(f"Failed to search YouTube for {query}: {e}")
        return f"Failed to search YouTube for '{query}'. Error: {str(e)}"

def fill_form(selector: str, value: str) -> str:
    """Fills an input field on the current page with a value."""
    try:
        page = browser_manager.get_page()
        element = page.locator(selector).first
        if not element.is_visible(timeout=3000):
            return f"Element with selector '{selector}' not found or not visible."
            
        element.fill(value)
        logger.success(f"Filled '{selector}' with '{value}'")
        return f"Successfully filled the input field."
    except Exception as e:
        logger.error(f"Failed to fill form {selector}: {e}")
        return f"Failed to fill form. Error: {str(e)}"

def switch_tab(index: int) -> str:
    """Switches to the browser tab at the given index (0-based)."""
    try:
        manager = browser_manager
        if not manager._context:
            return "No browser window is currently open."
            
        pages = manager._context.pages
        if not pages:
            return "No tabs are currently open."
            
        if index < 0 or index >= len(pages):
            return f"Invalid tab index {index}. There are only {len(pages)} open tabs."
            
        manager._page = pages[index]
        manager._page.bring_to_front()
        title = manager._page.title()
        
        logger.success(f"Switched to tab {index} ({title})")
        return f"Switched to tab {index}. Page title is '{title}'."
    except Exception as e:
        logger.error(f"Failed to switch tab: {e}")
        return f"Failed to switch tab. Error: {str(e)}"

def close_browser() -> str:
    """Closes the Playwright browser."""
    try:
        browser_manager.close()
        return "Successfully closed the browser."
    except Exception as e:
        return f"Failed to close browser: {str(e)}"
