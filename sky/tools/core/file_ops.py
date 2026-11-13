import os
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool
from sky.config import WORKSPACE_DIR

def _resolve_path(path_str: str) -> Path:
    p = Path(os.path.expanduser(path_str))
    if not p.is_absolute():
        p = WORKSPACE_DIR / p
    return p.resolve()

@tool
def read_file(path: str, max_lines: int = 300) -> str:
    """
    Read content of a file on the laptop.
    
    Args:
        path: Absolute or relative file path (relative resolves against workspace).
        max_lines: Maximum number of lines to return.
    """
    file_path = _resolve_path(path)
    if not file_path.exists():
        return f"Error: File '{file_path}' does not exist."
    if not file_path.is_file():
        return f"Error: '{file_path}' is a directory, not a file."
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines)]
            content = "".join(lines)
            return f"--- Content of {file_path} ---\n{content}"
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"

@tool
def write_file(path: str, content: str, append: bool = False) -> str:
    """
    Create or write content to a file on the laptop.
    
    Args:
        path: Path where the file should be written.
        content: The text content to write.
        append: If True, append to existing content instead of overwriting.
    """
    file_path = _resolve_path(path)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)
        action = "Appended to" if append else "Created/Updated"
        return f"Successfully {action} file: {file_path} ({len(content)} characters)."
    except Exception as e:
        return f"Error writing to file '{file_path}': {str(e)}"

@tool
def list_directory(path: Optional[str] = None) -> str:
    """
    List files and folders in a directory.
    
    Args:
        path: Optional directory path. Defaults to workspace directory.
    """
    dir_path = _resolve_path(path) if path else WORKSPACE_DIR
    if not dir_path.exists():
        return f"Error: Directory '{dir_path}' does not exist."
    if not dir_path.is_dir():
        return f"Error: '{dir_path}' is not a directory."
        
    try:
        entries = []
        for item in sorted(dir_path.iterdir()):
            prefix = "[DIR] " if item.is_dir() else "[FILE]"
            entries.append(f"{prefix} {item.name}")
        output = f"Contents of {dir_path}:\n" + ("\n".join(entries) if entries else "(Directory is empty)")
        return output
    except Exception as e:
        return f"Error listing directory '{dir_path}': {str(e)}"
