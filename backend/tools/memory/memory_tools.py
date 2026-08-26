from backend.memory.db import add_memory, remove_memory

def remember(category: str, label: str, value: str) -> str:
    """
    Saves an important fact, preference, or context to long-term memory.
    If the category and label already exist, it overwrites the value.
    """
    add_memory(category, label, value)
    return f"Memory saved successfully! Category: {category}, Label: {label}, Value: {value}"

def forget(label: str) -> str:
    """Removes a memory by its label."""
    success = remove_memory(label)
    if success:
        return f"Memory with label '{label}' has been forgotten."
    else:
        return f"Could not find any memory with label '{label}' to forget."
