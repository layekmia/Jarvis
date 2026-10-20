import asyncio
import json
import os
import re
import uuid
from loguru import logger

# Module-level registry to persist background processes
active_processes = {}

async def run_terminal_command(command: str, cwd: str, ready_pattern: str = None, timeout_seconds: int = 300) -> str:
    """
    Runs a shell command in the background, waits for a ready_pattern, and returns the result.
    If ready_pattern is not found within timeout_seconds, it returns a timeout status.
    """
    logger.info(f"[Terminal] Running command in {cwd}: {command}")
    
    if not os.path.exists(cwd):
        return json.dumps({"status": "error", "output": f"Directory not found: {cwd}"})

    try:
        # Prepare environment to prevent TTY errors in tools like pnpm
        env = os.environ.copy()
        env["CI"] = "true"
        env["FORCE_COLOR"] = "1"
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT, # Merge stderr into stdout
            stdin=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )
        
        process_id = str(uuid.uuid4())
        active_processes[process_id] = process
        logger.info(f"[Terminal] Process started with internal ID: {process_id}")

        if not ready_pattern:
            # If no pattern to wait for, just return that it's running
            return json.dumps({"status": "running", "process_id": process_id})

        output_buffer = []
        detected_port = None
        
        async def read_output():
            nonlocal detected_port
            pattern_regex = re.compile(ready_pattern, re.IGNORECASE)
            # Basic regex to catch localhost urls like http://localhost:5173 or http://127.0.0.1:3000
            port_regex = re.compile(r"http://(?:localhost|127\.0\.0\.1):(\d+)", re.IGNORECASE)
            
            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode('utf-8', errors='replace')
                line_str = line.strip()
                output_buffer.append(line_str)
                logger.debug(f"[Terminal Output] {line_str}")
                
                # Auto-answer yes to common (Y/n) prompts
                if "(Y/n)" in line_str or "[Y/n]" in line_str or "(y/N)" in line_str or "[y/N]" in line_str:
                    logger.info("[Terminal] Detected Y/n prompt. Auto-answering 'y'.")
                    if process.stdin:
                        process.stdin.write(b"y\n")
                        await process.stdin.drain()
                
                # Check for port
                port_match = port_regex.search(line)
                if port_match:
                    detected_port = port_match.group(1)
                
                # Check for ready pattern
                if pattern_regex.search(line):
                    return True # Ready pattern matched
            return False

        try:
            matched = await asyncio.wait_for(read_output(), timeout=timeout_seconds)
            if matched:
                logger.success(f"[Terminal] Ready pattern '{ready_pattern}' matched.")
                return json.dumps({
                    "status": "ready", 
                    "process_id": process_id,
                    "port": detected_port,
                    "last_output": "\n".join(output_buffer[-5:])
                })
            else:
                # Process exited before matching
                return json.dumps({
                    "status": "error", 
                    "output": "\n".join(output_buffer),
                    "reason": "Process exited before ready pattern was found."
                })
        except asyncio.TimeoutError:
            logger.warning(f"[Terminal] Timeout waiting for '{ready_pattern}'")
            return json.dumps({
                "status": "timeout",
                "process_id": process_id,
                "last_output": "\n".join(output_buffer[-10:]),
                "reason": f"Timed out after {timeout_seconds} seconds waiting for '{ready_pattern}'"
            })
            
    except Exception as e:
        logger.error(f"[Terminal] Failed to run command: {e}")
        return json.dumps({"status": "error", "output": str(e)})

async def stop_terminal_command(process_id: str) -> str:
    """Stops a background process by its internal ID."""
    if process_id in active_processes:
        process = active_processes[process_id]
        try:
            process.terminate()
            del active_processes[process_id]
            logger.info(f"[Terminal] Terminated process {process_id}")
            return json.dumps({"status": "success", "message": f"Terminated process {process_id}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Failed to terminate: {e}"})
    return json.dumps({"status": "error", "message": "Process not found in registry"})
