import pyautogui
import os
import time
from datetime import datetime
from loguru import logger
from backend.core.config import settings

# Fail-safe feature of PyAutoGUI to prevent runaway mouse movements
pyautogui.FAILSAFE = True

def type_text(text: str) -> str:
    """Types the given text as if using the keyboard."""
    try:
        # Provide a small delay before typing to ensure the window is ready
        time.sleep(0.5)
        pyautogui.write(text, interval=0.01)
        logger.success(f"Typed text length: {len(text)}")
        return f"Successfully typed the provided text."
    except Exception as e:
        logger.error(f"Failed to type text: {e}")
        return f"Failed to type text: {str(e)}"

def mouse_click(x: int = None, y: int = None) -> str:
    """Clicks the mouse at the given x, y coordinates, or at current position if None."""
    try:
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y)
            logger.success(f"Clicked at ({x}, {y})")
            return f"Successfully clicked at ({x}, {y})."
        else:
            pyautogui.click()
            logger.success("Clicked at current mouse position")
            return "Successfully clicked at the current mouse position."
    except Exception as e:
        logger.error(f"Failed to click: {e}")
        return f"Failed to perform mouse click: {str(e)}"

def take_screenshot() -> str:
    """Takes a screenshot and saves it to a local folder."""
    try:
        # Create a screenshots directory if it doesn't exist
        os.makedirs("screenshots", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/screenshot_{timestamp}.png"
        
        pyautogui.screenshot(filename)
        logger.success(f"Screenshot saved to {filename}")
        
        # We only return the success message to the AI
        return f"Screenshot successfully taken and saved as {filename}."
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return f"Failed to take screenshot: {str(e)}"
