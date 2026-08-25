import os
import subprocess
import pygetwindow as gw
from loguru import logger
import psutil

# Common aliases for Windows applications
APP_ALIASES = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "vs code": "code.exe",
    "vscode": "code.exe",
    "code": "code.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
}

def open_app(name: str) -> str:
    """Opens an application by name on Windows."""
    name_lower = name.lower().strip()
    
    # Check if we have an alias
    executable = APP_ALIASES.get(name_lower, name_lower)
    
    try:
        # Use Windows 'start' command which resolves PATH and App Paths in registry
        # We run it detached
        subprocess.Popen(f"start {executable}", shell=True)
        logger.success(f"Opened application: {executable}")
        return f"Successfully opened {name}."
    except Exception as e:
        logger.error(f"Failed to open application '{name}': {e}")
        return f"Failed to open {name}. Error: {str(e)}"

def close_app(name: str) -> str:
    """Closes an application gracefully using psutil."""
    name_lower = name.lower().strip()
    executable = APP_ALIASES.get(name_lower, name_lower)
    
    # Ensure it ends with .exe for matching process names
    if not executable.endswith(".exe"):
        executable += ".exe"
        
    closed_count = 0
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == executable:
                    proc.terminate()
                    closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if closed_count > 0:
            logger.success(f"Closed {closed_count} instances of {executable}")
            return f"Successfully closed {name}."
        else:
            # Fallback to taskkill
            result = subprocess.run(f"taskkill /F /IM {executable}", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.success(f"Closed {executable} using taskkill")
                return f"Successfully closed {name}."
            else:
                logger.warning(f"Could not find any running process for {name}")
                return f"Could not find any running application named {name} to close."
    except Exception as e:
        logger.error(f"Error closing {name}: {e}")
        return f"An error occurred while trying to close {name}."

def switch_app(name: str) -> str:
    """Brings an application window to the foreground."""
    try:
        # Search for windows containing the name
        windows = gw.getWindowsWithTitle(name)
        if not windows:
            return f"Could not find any open window containing the name '{name}'."
            
        # Try to focus the first match
        win = windows[0]
        
        # If window is minimized, restore it
        if win.isMinimized:
            win.restore()
            
        win.activate()
        logger.success(f"Switched focus to window: {win.title}")
        return f"Switched focus to {name}."
    except Exception as e:
        logger.error(f"Failed to switch to {name}: {e}")
        return f"Failed to switch to {name}. It may require manual focus."
