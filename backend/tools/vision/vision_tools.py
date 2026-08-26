"""
Phase 9 — Vision Tools
These tools allow Jarvis to "see" the screen and interact with it based on visual context.
"""

import os
import pyautogui
from datetime import datetime
from loguru import logger

from backend.ai.vision import VisionEngine, encode_image_to_base64
from backend.core.config import settings

def _capture_screen() -> str:
    """Takes a screenshot and returns the file path."""
    os.makedirs("screenshots", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshots/vision_{timestamp}.png"
    pyautogui.screenshot(filename)
    return filename

async def describe_screen(question: str) -> str:
    """Takes a screenshot and asks the vision model a question about it."""
    try:
        image_path = _capture_screen()
        base64_image = encode_image_to_base64(image_path)
        
        # Broadcast to frontend
        from backend.api.main import broadcast_event
        await broadcast_event("vision_capture", {
            "image_base64": f"data:image/png;base64,{base64_image}",
            "action": "Describe Screen",
            "details": f"Question: {question}"
        })
        
        engine = VisionEngine(api_key=settings.openai_api_key)
        description = await engine.describe_image(image_path, question)
        
        # Optionally broadcast the result back
        await broadcast_event("vision_result", {
            "result": description
        })
        
        return f"Vision result: {description}"
    except Exception as e:
        logger.error(f"Failed to describe screen: {e}")
        return f"Failed to describe screen: {str(e)}"

async def click_element_on_screen(element_description: str) -> str:
    """Finds an element by description and clicks it."""
    try:
        image_path = _capture_screen()
        base64_image = encode_image_to_base64(image_path)
        
        # Broadcast to frontend
        from backend.api.main import broadcast_event
        await broadcast_event("vision_capture", {
            "image_base64": f"data:image/png;base64,{base64_image}",
            "action": "Find & Click",
            "details": f"Target: {element_description}"
        })
        
        engine = VisionEngine(api_key=settings.openai_api_key)
        coords = await engine.find_element(image_path, element_description)
        
        if coords:
            x, y = coords["x"], coords["y"]
            pyautogui.click(x=x, y=y)
            
            result_msg = f"Successfully clicked '{element_description}' at coordinates ({x}, {y})."
            await broadcast_event("vision_result", {
                "result": result_msg
            })
            return result_msg
        else:
            err_msg = f"Could not locate '{element_description}' on the screen."
            await broadcast_event("vision_result", {
                "result": err_msg
            })
            return err_msg
    except Exception as e:
        logger.error(f"Failed to click element on screen: {e}")
        return f"Failed to click element on screen: {str(e)}"
