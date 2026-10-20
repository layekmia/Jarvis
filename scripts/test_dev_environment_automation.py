import asyncio
import os
import json
import tempfile
import shutil
from loguru import logger

# Import the tools directly
from backend.tools.automation.terminal import run_terminal_command, stop_terminal_command
from backend.tools.automation.web_verify import verify_url
from backend.ai.agentic_planner import AgenticPlanner, TaskStep

async def dummy_broadcast(event, data):
    logger.info(f"Broadcast: {event} -> {json.dumps(data, indent=2)}")

async def main():
    logger.info("Setting up dummy project...")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock package.json (Vite)
        pkg_json = {
            "name": "mock-vite-project",
            "dependencies": {
                "vite": "^4.0.0"
            }
        }
        with open(os.path.join(temp_dir, "package.json"), "w") as f:
            json.dump(pkg_json, f)
            
        # Create a mock python script that acts like a dev server
        mock_server = """import time, sys
print("starting up...")
sys.stdout.flush()
time.sleep(2)
print("VITE v4.0.0 ready in 1500 ms")
print("  ➜  Local:   http://localhost:8080/")
sys.stdout.flush()
while True:
    time.sleep(1)
"""
        with open(os.path.join(temp_dir, "mock_server.py"), "w", encoding="utf-8") as f:
            f.write(mock_server)
            
        logger.info("Initializing Planner...")
        planner = AgenticPlanner()
        
        # We will mock the TOOL_MAP
        tool_map = {
            "run_terminal_command": run_terminal_command,
            "verify_url": verify_url
        }
        
        steps = [
            TaskStep(
                id=1,
                description="Run the dev server",
                tool="run_terminal_command",
                args={
                    "command": "python mock_server.py",
                    "cwd": temp_dir,
                    "timeout_seconds": 10
                }
            ),
            TaskStep(
                id=2,
                description="Verify the server is up",
                tool="verify_url",
                args={
                    "url": "http://localhost:{port}"
                }
            )
        ]
        
        logger.info("Running AgenticPlanner task chain...")
        result = await planner.run(
            task="Start dev server and verify",
            steps=steps,
            tool_map=tool_map,
            tts_engine=None,
            player=None,
            broadcast_callback=dummy_broadcast
        )
        
        logger.info(f"Final Result: {result}")
        
        # Verify if verify_url failed gracefully (since mock server doesn't actually serve HTTP)
        # We expect the task to fail at step 2, but step 1 should succeed and capture port 8080.
        
        # Clean up process
        logger.info("Cleaning up background processes...")
        # (In a real scenario, we would use the process registry)
        
if __name__ == "__main__":
    asyncio.run(main())
