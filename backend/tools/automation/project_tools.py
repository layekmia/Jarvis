import json
import subprocess
import os
from loguru import logger

def open_project(path: str, editor: str = "antigravity") -> str:
    """
    Opens a project directory in the specified IDE/editor.
    Supports "code" (VS Code) and "antigravity" (AGY CLI).
    """
    path = os.path.normpath(path)
    logger.info(f"[ProjectTools] Opening project {path} with editor '{editor}'")
    
    if not os.path.exists(path):
        return json.dumps({"status": "error", "message": f"Path does not exist: {path}"})
    
    try:
        if editor.lower() == "antigravity":
            # Spawn a new Git Bash window running agy interactive TUI
            git_bash_path = "C:\\Program Files\\Git\\git-bash.exe"
            if os.path.exists(git_bash_path):
                # use exec bash so the window stays open after agy exits
                cmd = f'start "" "{git_bash_path}" --cd="{path}" -c "agy; exec bash"'
            else:
                # Fallback to cmd if Git Bash is missing
                cmd = f'start cmd /k "cd /d \"{path}\" && agy"'
                
            subprocess.Popen(cmd, shell=True)
            return json.dumps({"status": "success", "message": f"Opened {path} in Antigravity"})
            
        else:
            # Default to VS Code
            subprocess.Popen(["code", path], shell=True)
            return json.dumps({"status": "success", "message": f"Opened {path} in VS Code"})
            
    except Exception as e:
        logger.error(f"[ProjectTools] Failed to open project: {e}")
        return json.dumps({"status": "error", "message": str(e)})
