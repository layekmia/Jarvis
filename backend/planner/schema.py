from typing import Any

# OpenAI Function Calling Schema for Phase 4 + Phase 5 Tools

TOOLS_SCHEMA: list[dict[str, Any]] = [

    # ── Phase 4: Computer Control ─────────────────────────────────────────────

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
    },

    # ── Phase 5: File System Tools ────────────────────────────────────────────

    {
        "type": "function",
        "function": {
            "name": "search_file",
            "description": (
                "Searches for files or folders by name (supports glob patterns like *.py). "
                "Searches within the user's home directory by default."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Filename or glob pattern to search for, e.g. 'report.pdf' or '*.txt'."
                    },
                    "search_in": {
                        "type": "string",
                        "description": "Optional absolute directory path to restrict the search to."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return. Defaults to 10."
                    }
                },
                "required": ["query"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Creates a new file at the specified path, optionally with text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path for the new file, e.g. 'C:/Users/user/Desktop/notes.txt'."
                    },
                    "content": {
                        "type": "string",
                        "description": "Optional text content to write into the new file."
                    }
                },
                "required": ["path"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_summary",
            "description": (
                "Reads a text file and returns a summary of its content along with metadata "
                "(size, last modified date). Does not work on binary files like images or executables."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file to read."
                    }
                },
                "required": ["path"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copies a file or folder to a new destination path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Absolute path of the file or folder to copy."
                    },
                    "destination": {
                        "type": "string",
                        "description": "Absolute destination path."
                    }
                },
                "required": ["source", "destination"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": (
                "Moves a file or folder to a new location. "
                "This is a potentially destructive action — Jarvis will ask for user confirmation before proceeding."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Absolute path of the file or folder to move."
                    },
                    "destination": {
                        "type": "string",
                        "description": "Absolute destination path."
                    }
                },
                "required": ["source", "destination"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": (
                "Renames a file or folder. "
                "This is a potentially destructive action — Jarvis will ask for user confirmation before proceeding."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path of the file or folder to rename."
                    },
                    "new_name": {
                        "type": "string",
                        "description": "The new filename (just the name portion, not a full path)."
                    }
                },
                "required": ["path", "new_name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": (
                "Permanently deletes a file or folder. "
                "ALWAYS requires user confirmation — Jarvis will always ask before deleting anything."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path of the file or folder to delete."
                    }
                },
                "required": ["path"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists all files and folders inside a given directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path of the directory to list."
                    }
                },
                "required": ["path"],
            },
        }
    },

    # ── Phase 6: Browser Automation Tools ─────────────────────────────────────

    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Opens a given URL in the web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to open, e.g. 'https://example.com'."
                    }
                },
                "required": ["url"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches Google for the given query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_search",
            "description": "Searches YouTube for the given query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The video search query."
                    }
                },
                "required": ["query"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fill_form",
            "description": "Fills an input field on the current web page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "The CSS selector of the input field to fill."
                    },
                    "value": {
                        "type": "string",
                        "description": "The value to fill in the field."
                    }
                },
                "required": ["selector", "value"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_tab",
            "description": "Switches to an open browser tab by index (0-based).",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                        "description": "The 0-based index of the tab to switch to."
                    }
                },
                "required": ["index"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_browser",
            "description": "Closes the browser window.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
    },
]
