"""
Phase 9 — Vision Engine
Handles sending screenshots to the OpenAI Vision API and parsing the results.
"""

import base64
import json
from typing import Any, Optional
from loguru import logger
from openai import AsyncOpenAI
from backend.core.config import settings

# Usually, we'd use gpt-4o or gpt-4-turbo for vision.
# We will use the model specified in the settings, falling back to gpt-4o.
VISION_MODEL = "gpt-4o"


def encode_image_to_base64(image_path: str) -> str:
    """Reads an image file and returns its base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


class VisionEngine:
    """Wrapper for OpenAI's Vision capabilities."""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.openai_base_url if settings.openai_base_url else None
        )
        self.model = VISION_MODEL
        
    async def describe_image(self, image_path: str, question: str) -> str:
        """
        Sends an image to the vision model and asks a question about it.
        """
        logger.info(f"[Vision] Describing image {image_path} with question: '{question}'")
        try:
            base64_image = encode_image_to_base64(image_path)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.5
            )
            description = response.choices[0].message.content.strip()
            logger.info(f"[Vision] Description result: {description}")
            return description
        except Exception as e:
            logger.error(f"[Vision] Error describing image: {e}")
            return f"Failed to analyze the screen: {str(e)}"
            
    async def find_element(self, image_path: str, element_desc: str) -> Optional[dict[str, int]]:
        """
        Finds the (x, y) coordinates of a described element on the screen.
        Expects the LLM to return JSON with 'x' and 'y' keys.
        """
        logger.info(f"[Vision] Finding element '{element_desc}' on {image_path}")
        
        prompt = f"""
You are an expert UI locator. Your task is to find the element described as '{element_desc}' in the provided screenshot.
Analyze the image carefully and estimate the (x, y) pixel coordinates of the center of that element.
The image resolution is assumed to be 1920x1080 (standard 1080p).
Return ONLY a valid JSON object with 'x' and 'y' integer coordinates. No markdown, no explanation.

Example:
{{"x": 500, "y": 250}}
"""
        
        try:
            base64_image = encode_image_to_base64(image_path)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={ "type": "json_object" },
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100,
                temperature=0.1
            )
            result_str = response.choices[0].message.content.strip()
            logger.info(f"[Vision] Coordinates result: {result_str}")
            
            data = json.loads(result_str)
            if "x" in data and "y" in data:
                return {"x": int(data["x"]), "y": int(data["y"])}
            return None
        except Exception as e:
            logger.error(f"[Vision] Error finding element: {e}")
            return None
