from typing import Any

# OpenAI Function Calling Schema for Phase 4 + Phase 5 Tools

TOOLS_SCHEMA: list[dict[str, Any]] = [

    # ── Phase 4: Computer Control ─────────────────────────────────────────────

    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": (
                "Opens an application on the user's Windows computer by its name. "
                "For Chrome or Edge, also accepts an optional 'profile' argument to open "
                "a specific browser profile (e.g. 'Layek', 'Rasel'). "
                "If 'profile' is omitted, the last-used profile is used automatically — "
                "no profile picker will appear."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the application to open (e.g., 'notepad', 'chrome', 'calculator')."
                    },
                    "profile": {
                        "type": "string",
                        "description": (
                            "Optional. For Chrome or Edge only. "
                            "The display name of the browser profile to open "
                            "(e.g. 'Layek', 'Rasel', 'Entertop'). "
                            "Omit this if the user did not specify a profile."
                        )
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
            "description": "Takes a screenshot of the main screen and saves it.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_system",
            "description": "Shuts down the user's computer with a 60-second delay.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_system",
            "description": "Restarts the user's computer with a 60-second delay.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
    },

    # ── Phase 5: File Operations ──────────────────────────────────────────────

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
            "description": (
                "Opens YouTube search results for the given query in Chrome (with the user's logged-in profile). "
                "Use this when the user wants to browse or find videos — NOT when they want to immediately play a specific song/video. "
                "For playing a specific song or video, use youtube_play instead."
            ),
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
            "name": "youtube_play",
            "description": (
                "Plays a specific song, video, or any YouTube content directly in Chrome. "
                "Use this when the user says 'play [song name]', 'chalao', 'gaan ta play koro', or wants to watch something specific. "
                "It finds the best matching video and opens it directly — no searching needed. "
                "ALWAYS prefer this over youtube_search when the user's intent is to play/watch something."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The song name, artist, or video title to play (e.g. 'Mufi', 'Shape of You', 'Arijit Singh tum hi ho')."
                    }
                },
                "required": ["query"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_open",
            "description": (
                "Opens the YouTube homepage in Chrome with the user's logged-in profile. "
                "Use this when the user says 'open YouTube', 'YouTube kholo', or wants to go to YouTube without a specific video."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
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

    # ── Phase 7: Memory Tools ─────────────────────────────────────────────────

    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Saves an important fact, user preference, or context to long-term memory. Use this spontaneously when the user shares personal info or preferences, even if they don't explicitly say 'remember'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["context", "preference", "task", "fact"],
                        "description": "The category of the memory."
                    },
                    "label": {
                        "type": "string",
                        "description": "A short, unique label for this memory (e.g., 'user_name', 'favorite_color')."
                    },
                    "value": {
                        "type": "string",
                        "description": "The actual information to remember."
                    }
                },
                "required": ["category", "label", "value"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forget",
            "description": "Removes a memory from long-term memory by its label.",
            "parameters": {
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "The label of the memory to forget."
                    }
                },
                "required": ["label"],
            },
        }
    },

    # ── Phase 9: Vision Tools ─────────────────────────────────────────────────

    {
        "type": "function",
        "function": {
            "name": "describe_screen",
            "description": "Takes a screenshot of the user's computer screen and uses visual intelligence to answer a question about what is currently visible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask the vision model about the screen."
                    }
                },
                "required": ["question"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_element_on_screen",
            "description": "Takes a screenshot, visually locates an element described by the user, and clicks its (x, y) coordinates on the screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_description": {
                        "type": "string",
                        "description": "A description of the UI element to click (e.g. 'the submit button', 'the search bar')."
                    }
                },
                "required": ["element_description"],
            },
        }
    },
]
