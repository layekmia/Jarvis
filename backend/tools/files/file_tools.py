"""
Phase 5 — File System Control Tools

All operations are Windows-compatible and have proper error handling.
Destructive actions (delete, move, rename) return a special CONFIRM_NEEDED
response that the WebSocket layer uses to trigger a UI confirmation prompt.
"""

import os
import shutil
import fnmatch
import datetime
from pathlib import Path
from typing import Optional
from loguru import logger

# ── Constants ──────────────────────────────────────────────────────────────────

# Directories that Jarvis is allowed to operate in by default.
# Prevents accidental writes to system dirs.
ALLOWED_ROOTS: list[Path] = [
    Path.home(),                            # C:\Users\<user>
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Pictures",
    Path.home() / "Music",
    Path.home() / "Videos",
]

# Extensions to skip when summarising (binary/executable/etc.)
BINARY_EXTENSIONS: set[str] = {
    ".exe", ".dll", ".so", ".bin", ".dat", ".db", ".sqlite",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".wav",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".pdf", ".docx", ".xlsx", ".pptx",
}

# Max characters to read when summarising a text file
SUMMARY_MAX_CHARS: int = 2000

# Sentinel prefix used by the planner to know a confirmation is needed
CONFIRM_PREFIX: str = "CONFIRM_NEEDED:"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_path_safe(path: Path) -> bool:
    """Returns True if path is inside one of the ALLOWED_ROOTS."""
    try:
        resolved = path.resolve()
        for root in ALLOWED_ROOTS:
            try:
                resolved.relative_to(root.resolve())
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False


def _format_size(size_bytes: int) -> str:
    """Human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


# ── Tool Functions ─────────────────────────────────────────────────────────────

def search_file(
    query: str,
    search_in: Optional[str] = None,
    max_results: int = 10,
) -> str:
    """
    Searches for files and folders matching a name pattern (glob supported).

    Args:
        query:      Filename or glob pattern, e.g. "report.pdf" or "*.py"
        search_in:  Optional absolute path to restrict the search. 
                    Defaults to the user's home directory.
        max_results: Maximum number of results to return.

    Returns:
        Human-readable string listing matching paths, or an error message.
    """
    base = Path(search_in) if search_in else Path.home()

    if not base.exists() or not base.is_dir():
        logger.warning(f"search_file: path not found or not a dir: {base}")
        return f"Search directory '{base}' does not exist or is not accessible."

    if not _is_path_safe(base):
        logger.warning(f"search_file: path outside allowed roots: {base}")
        return f"Search in '{base}' is not allowed for safety reasons."

    logger.info(f"Searching for '{query}' in '{base}'...")
    matches: list[str] = []

    try:
        for root_dir, dirs, files in os.walk(base):
            # Skip hidden directories (e.g. .git, .venv)
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            all_entries = dirs + files
            for entry in all_entries:
                if fnmatch.fnmatch(entry.lower(), query.lower()):
                    full = os.path.join(root_dir, entry)
                    matches.append(full)
                    if len(matches) >= max_results:
                        break
            if len(matches) >= max_results:
                break
    except PermissionError as e:
        logger.error(f"Permission denied during search: {e}")
        return f"Permission denied while searching in '{base}'. Try a more specific directory."
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        return f"An error occurred during the file search: {str(e)}"

    if not matches:
        return f"No files or folders matching '{query}' were found in '{base}'."

    result_lines = [f"Found {len(matches)} result(s) for '{query}':"]
    for m in matches:
        result_lines.append(f"  • {m}")
    if len(matches) >= max_results:
        result_lines.append(f"  (Showing first {max_results} results. Be more specific to narrow down.)")

    logger.success(f"search_file: found {len(matches)} matches for '{query}'")
    return "\n".join(result_lines)


def create_file(path: str, content: str = "") -> str:
    """
    Creates a new file (and any missing parent directories) at the given path.

    Args:
        path:    Absolute or home-relative path for the new file.
        content: Optional text content to write into the file.

    Returns:
        Success or error message.
    """
    target = Path(path).expanduser()

    if not _is_path_safe(target):
        logger.warning(f"create_file: blocked unsafe path: {target}")
        return f"Creating files outside your home directory is not allowed."

    if target.exists():
        logger.warning(f"create_file: file already exists: {target}")
        return f"A file already exists at '{target}'. Use a different name or path."

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.success(f"Created file: {target}")
        return f"File created successfully at '{target}'."
    except PermissionError:
        logger.error(f"create_file: permission denied for {target}")
        return f"Permission denied. Cannot create file at '{target}'."
    except Exception as e:
        logger.error(f"create_file failed: {e}")
        return f"Failed to create file: {str(e)}"


def read_file_summary(path: str) -> str:
    """
    Reads and summarises the content of a text file.

    Args:
        path: Absolute path to the file to read.

    Returns:
        File metadata + truncated content, or an error message.
    """
    target = Path(path).expanduser()

    if not target.exists():
        return f"File not found: '{target}'"

    if not target.is_file():
        return f"'{target}' is a directory, not a file."

    if not _is_path_safe(target):
        return f"Reading files outside your home directory is not allowed."

    suffix = target.suffix.lower()
    if suffix in BINARY_EXTENSIONS:
        try:
            stat = target.stat()
            return (
                f"File: {target.name}\n"
                f"Size: {_format_size(stat.st_size)}\n"
                f"Type: Binary / {suffix} file — content cannot be displayed as text."
            )
        except Exception as e:
            return f"Could not read file metadata: {str(e)}"

    try:
        stat = target.stat()
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        content = target.read_text(encoding="utf-8", errors="replace")

        truncated = False
        if len(content) > SUMMARY_MAX_CHARS:
            content = content[:SUMMARY_MAX_CHARS]
            truncated = True

        summary = (
            f"File: {target.name}\n"
            f"Path: {target}\n"
            f"Size: {_format_size(stat.st_size)} | Last modified: {modified}\n"
            f"---\n"
            f"{content}"
        )
        if truncated:
            summary += f"\n... [truncated — file has more content]"

        logger.info(f"read_file_summary: read {target.name}")
        return summary
    except PermissionError:
        return f"Permission denied. Cannot read '{target}'."
    except Exception as e:
        logger.error(f"read_file_summary failed: {e}")
        return f"Failed to read file: {str(e)}"


def move_file(source: str, destination: str) -> str:
    """
    Moves a file or folder to a new location.
    Returns a CONFIRM_NEEDED sentinel — the caller must get user approval first.

    Args:
        source:      Absolute path of the file/folder to move.
        destination: Absolute path of the destination directory or new full path.

    Returns:
        CONFIRM_NEEDED string with details, or success/error message if already confirmed.
    """
    src = Path(source).expanduser()
    dst = Path(destination).expanduser()

    if not src.exists():
        return f"Source path not found: '{src}'"

    if not _is_path_safe(src) or not _is_path_safe(dst):
        return "Moving files outside your home directory is not allowed."

    # Emit confirmation sentinel — the planner will intercept this
    return (
        f"{CONFIRM_PREFIX} Move '{src.name}' from '{src.parent}' to '{dst}'? "
        f"[source={source}|destination={destination}|action=move_file_confirmed]"
    )


def move_file_confirmed(source: str, destination: str) -> str:
    """
    Actually executes the file move after user confirms.

    Args:
        source:      Absolute path of the file/folder to move.
        destination: Absolute destination path.
    """
    src = Path(source).expanduser()
    dst = Path(destination).expanduser()

    if not src.exists():
        return f"Source no longer found: '{src}'"

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        logger.success(f"Moved '{src}' → '{dst}'")
        return f"Successfully moved '{src.name}' to '{dst}'."
    except PermissionError:
        logger.error(f"move_file: permission denied")
        return f"Permission denied. Cannot move '{src.name}'."
    except Exception as e:
        logger.error(f"move_file_confirmed failed: {e}")
        return f"Failed to move file: {str(e)}"


def copy_file(source: str, destination: str) -> str:
    """
    Copies a file or folder to a new location.

    Args:
        source:      Absolute path of the file/folder to copy.
        destination: Absolute destination path.

    Returns:
        Success or error message.
    """
    src = Path(source).expanduser()
    dst = Path(destination).expanduser()

    if not src.exists():
        return f"Source path not found: '{src}'"

    if not _is_path_safe(src) or not _is_path_safe(dst):
        return "Copying files outside your home directory is not allowed."

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(str(src), str(dst))
            logger.success(f"Copied directory '{src}' → '{dst}'")
        else:
            shutil.copy2(str(src), str(dst))
            logger.success(f"Copied file '{src}' → '{dst}'")
        return f"Successfully copied '{src.name}' to '{dst}'."
    except FileExistsError:
        return f"Destination already exists: '{dst}'. Choose a different name."
    except PermissionError:
        logger.error(f"copy_file: permission denied")
        return f"Permission denied. Cannot copy to '{dst}'."
    except Exception as e:
        logger.error(f"copy_file failed: {e}")
        return f"Failed to copy: {str(e)}"


def rename_file(path: str, new_name: str) -> str:
    """
    Renames a file or folder. Returns a CONFIRM_NEEDED sentinel.

    Args:
        path:     Absolute path of the file/folder to rename.
        new_name: New filename (just the name, not a full path).

    Returns:
        CONFIRM_NEEDED string or error message.
    """
    src = Path(path).expanduser()

    if not src.exists():
        return f"File not found: '{src}'"

    if not _is_path_safe(src):
        return "Renaming files outside your home directory is not allowed."

    if "/" in new_name or "\\" in new_name:
        return "New name must be a filename only, not a path."

    return (
        f"{CONFIRM_PREFIX} Rename '{src.name}' to '{new_name}'? "
        f"[path={path}|new_name={new_name}|action=rename_file_confirmed]"
    )


def rename_file_confirmed(path: str, new_name: str) -> str:
    """Executes the rename after user confirmation."""
    src = Path(path).expanduser()
    dst = src.parent / new_name

    if not src.exists():
        return f"File no longer found: '{src}'"

    if dst.exists():
        return f"A file named '{new_name}' already exists in the same folder."

    try:
        src.rename(dst)
        logger.success(f"Renamed '{src.name}' → '{new_name}'")
        return f"Successfully renamed '{src.name}' to '{new_name}'."
    except PermissionError:
        return f"Permission denied. Cannot rename '{src.name}'."
    except Exception as e:
        logger.error(f"rename_file_confirmed failed: {e}")
        return f"Failed to rename: {str(e)}"


def delete_file(path: str) -> str:
    """
    Deletes a file or folder. Returns a CONFIRM_NEEDED sentinel — always.

    Args:
        path: Absolute path of the file/folder to delete.

    Returns:
        CONFIRM_NEEDED string or error message.
    """
    target = Path(path).expanduser()

    if not target.exists():
        return f"Nothing to delete — path not found: '{path}'"

    if not _is_path_safe(target):
        return "Deleting files outside your home directory is not allowed."

    kind = "folder" if target.is_dir() else "file"
    return (
        f"{CONFIRM_PREFIX} Permanently delete {kind} '{target.name}' at '{target.parent}'? "
        f"This cannot be undone. [path={path}|action=delete_file_confirmed]"
    )


def delete_file_confirmed(path: str) -> str:
    """Executes the deletion after user confirmation."""
    target = Path(path).expanduser()

    if not target.exists():
        return f"Nothing to delete — path not found: '{path}'"

    if not _is_path_safe(target):
        return "Deleting files outside your home directory is not allowed."

    try:
        if target.is_dir():
            shutil.rmtree(target)
            logger.success(f"Deleted directory: {target}")
            return f"Folder '{target.name}' and all its contents have been deleted."
        else:
            target.unlink()
            logger.success(f"Deleted file: {target}")
            return f"File '{target.name}' has been deleted."
    except PermissionError:
        logger.error(f"delete_file: permission denied for {target}")
        return f"Permission denied. Cannot delete '{target.name}'."
    except Exception as e:
        logger.error(f"delete_file_confirmed failed: {e}")
        return f"Failed to delete: {str(e)}"


def list_directory(path: str) -> str:
    """
    Lists the contents of a directory.

    Args:
        path: Absolute path of the directory to list.

    Returns:
        Human-readable directory listing, or error message.
    """
    target = Path(path).expanduser()

    if not target.exists():
        return f"Directory not found: '{path}'"

    if not target.is_dir():
        return f"'{path}' is a file, not a directory."

    if not _is_path_safe(target):
        return "Listing directories outside your home directory is not allowed."

    try:
        entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        if not entries:
            return f"Directory '{target.name}' is empty."

        lines = [f"Contents of '{target}' ({len(entries)} items):"]
        for entry in entries[:50]:  # cap at 50 entries
            try:
                if entry.is_dir():
                    lines.append(f"  📁 {entry.name}/")
                else:
                    size = _format_size(entry.stat().st_size)
                    lines.append(f"  📄 {entry.name}  ({size})")
            except PermissionError:
                lines.append(f"  🔒 {entry.name}  (permission denied)")

        if len(entries) > 50:
            lines.append(f"  ... and {len(entries) - 50} more items.")

        logger.info(f"list_directory: listed {target}")
        return "\n".join(lines)
    except PermissionError:
        return f"Permission denied. Cannot list '{path}'."
    except Exception as e:
        logger.error(f"list_directory failed: {e}")
        return f"Failed to list directory: {str(e)}"
