import json
import httpx
import asyncio
from loguru import logger

async def verify_url(url: str) -> str:
    """
    Verifies that a given URL is reachable and returns a valid HTTP response (status 200).
    Retries a few times to allow servers that just started to fully boot up.
    """
    if not url.startswith("http"):
        url = "http://" + url

    logger.info(f"[WebVerify] Verifying URL: {url}")
    
    max_retries = 5
    delay_seconds = 2.0
    
    urls_to_try = [url]
    if "localhost" in url:
        urls_to_try.append(url.replace("localhost", "127.0.0.1"))
        
    async with httpx.AsyncClient(timeout=5.0) as client:
        for attempt in range(1, max_retries + 1):
            for test_url in urls_to_try:
                try:
                    response = await client.get(test_url)
                    if response.status_code == 200:
                        logger.success(f"[WebVerify] URL {test_url} verified successfully on attempt {attempt}.")
                        return json.dumps({"success": True})
                    else:
                        logger.warning(f"[WebVerify] URL {test_url} returned status {response.status_code} on attempt {attempt}.")
                except Exception as e:
                    logger.warning(f"[WebVerify] URL {test_url} failed on attempt {attempt}: {type(e).__name__} {e}")
                    
            if attempt < max_retries:
                await asyncio.sleep(delay_seconds)
                
    error_msg = f"Failed to verify {url} after {max_retries} attempts."
    logger.error(f"[WebVerify] {error_msg}")
    return json.dumps({"success": False, "reason": error_msg})
