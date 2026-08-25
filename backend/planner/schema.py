from typing import Any

# OpenAI Function Calling Schema for Phase 4 Tools

TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Opens an application on the user's Windows computer by its name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the application to open (e.g., 'notepad', 'chrome', 'calculator')."
                    }
                },
                "required": ["name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_app",
            "description": "Closes a running application on the user's computer by its name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the application to close."
                    }
                },
                "required": ["name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_app",
            "description": "Brings an open application window to the foreground.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name or title of the window/application to switch to."
                    }
                },
                "required": ["name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Adjusts the system volume to a specific level (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "The target volume level from 0 to 100."
                    }
                },
                "required": ["level"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_brightness",
            "description": "Adjusts the screen brightness to a specific level (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "The target brightness level from 0 to 100."
                    }
                },
                "required": ["level"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Retrieves the current CPU, RAM, and Battery usage statistics.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Simulates keyboard typing to input text into the currently focused window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to type."
                    }
                },
                "required": ["text"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Clicks the mouse. Can click at current position or specific x/y coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "Optional X coordinate to click."
                    },
                    "y": {
                        "type": "integer",
                        "description": "Optional Y coordinate to click."
                    }
                },
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Takes a screenshot of the main monitor and saves it.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
    }
]
