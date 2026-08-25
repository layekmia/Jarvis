from typing import Any

# OpenAI Function Calling Schema for Phase 3 Tools
# In future phases, these tools will be implemented with actual PyAutoGUI/Playwright actions.

TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Opens an application on the user's computer by its name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the application to open (e.g., 'notepad', 'chrome', 'calculator')."
                    }
                },
                "required": ["app_name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_app",
            "description": "Closes an application on the user's computer by its name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the application to close."
                    }
                },
                "required": ["app_name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Adjusts the system volume to a specific level or direction (up/down).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "The target volume level from 0 to 100."
                    },
                    "action": {
                        "type": "string",
                        "enum": ["up", "down", "mute", "unmute"],
                        "description": "Alternative to level: whether to turn it up, down, mute or unmute."
                    }
                },
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_file",
            "description": "Searches for a file by its name or query on the computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The file name or search query."
                    }
                },
                "required": ["query"],
            },
        }
    }
]
