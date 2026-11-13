import os
import glob
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import psutil
from langchain_core.tools import tool
from sky.config import WORKSPACE_DIR

def _find_recent_vscode_file() -> Optional[Path]:
    """Inspect VS Code state or workspace for the most recently touched file."""
    # Check VS Code workspace storage backups
    storage_pattern = os.path.expanduser("~/.config/Code/User/workspaceStorage/*/backup/file/*")
    recent_backups = glob.glob(storage_pattern)
    if recent_backups:
        latest = max(recent_backups, key=os.path.getmtime)
        try:
            with open(latest, "r", encoding="utf-8", errors="ignore") as f:
                first_line = f.readline().strip()
                if first_line.startswith("file://"):
                    p = Path(first_line.replace("file://", ""))
                    if p.exists() and p.is_file():
                        return p
        except Exception:
            pass

    # Check files inside workspace directory
    ws_files = [f for f in WORKSPACE_DIR.glob("*.*") if f.is_file() and not f.name.startswith(".")]
    if ws_files:
        return max(ws_files, key=os.path.getmtime)

    return None

def _resolve_file_path(path_str: Optional[str]) -> Tuple[Optional[Path], bool]:
    """
    Resolves file path. Returns (Path, was_explicitly_requested).
    """
    if not path_str or path_str.strip().lower() in ("none", "auto", "this file", "current file", ""):
        detected = _find_recent_vscode_file()
        return detected, False
    
    p = Path(os.path.expanduser(path_str.strip()))
    if not p.is_absolute():
        p = WORKSPACE_DIR / p
    return p.resolve(), True

@tool
def inspect_open_file_context() -> str:
    """
    Check if a file is currently open in VS Code or workspace and inspect its current content.
    Returns the file path and preview of what code is already written inside.
    """
    recent_file = _find_recent_vscode_file()
    if recent_file and recent_file.exists():
        try:
            with open(recent_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            preview = "".join(lines[:20])
            total_lines = len(lines)
            return (
                f"Active file detected: '{recent_file.name}' ({recent_file.resolve()})\n"
                f"Total lines: {total_lines}\n"
                f"Existing Code Preview:\n```python\n{preview}\n```\n"
                f"Note: When adding new code, keep existing functions intact unless asked to replace them."
            )
        except Exception as e:
            return f"Active file detected at '{recent_file}', but error reading content: {e}"

    return "No active file found currently open. Recommended to create a separate new .py file."

@tool
def create_new_code_file(
    filename: str,
    code_content: str,
    open_in_editor: bool = True
) -> str:
    """
    Create a brand new, separate code file in the workspace.
    Use this when the user asks for a new task or script (e.g. 'write hello world', 'write addition script')
    instead of touching existing files.
    
    Args:
        filename: Name for the new file (e.g., 'hello_world.py', 'calculator.py', 'primes.py').
        code_content: The Python code to write into the new file.
        open_in_editor: Whether to open the newly created file in VS Code.
    """
    clean_name = filename.strip()
    if not clean_name.endswith(".py") and "." not in clean_name:
        clean_name += ".py"

    target = WORKSPACE_DIR / clean_name
    
    # If file with this name already exists and has content, avoid overwriting!
    if target.exists() and target.stat().st_size > 0:
        base = target.stem
        ext = target.suffix
        counter = 2
        while (WORKSPACE_DIR / f"{base}_{counter}{ext}").exists():
            counter += 1
        target = WORKSPACE_DIR / f"{base}_{counter}{ext}"

    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(code_content.strip() + "\n")

    opened_info = ""
    if open_in_editor and shutil.which("code"):
        try:
            subprocess.Popen(["code", str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            opened_info = " and opened in VS Code"
        except Exception:
            pass

    return f"Created separate new file '{target.name}' at '{target}' ({len(code_content)} chars){opened_info}."

@tool
def add_code_to_file(
    code_to_add: str,
    file_path: Optional[str] = None,
    overwrite_existing: bool = False,
    open_in_editor: bool = True
) -> str:
    """
    Neatly add or append code to an existing file without destroying previously written code.
    If the file has existing code, it inspects it first and integrates the new code cleanly.
    
    Args:
        code_to_add: The new Python code, function, or logic to add.
        file_path: Target file path or name. If 'this file' or omitted, uses the currently active file.
        overwrite_existing: ONLY set True if the user explicitly asked to replace/overwrite the whole file. Default is False.
        open_in_editor: Whether to open/focus the file in VS Code.
    """
    resolved_path, was_explicit = _resolve_file_path(file_path)

    # If no file exists or was open, create a new separate file
    if not resolved_path:
        return create_new_code_file(
            filename="script.py",
            code_content=code_to_add,
            open_in_editor=open_in_editor
        )

    target = resolved_path

    # Read existing content if file exists
    existing_content = ""
    if target.exists():
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                existing_content = f.read().rstrip()
        except Exception as e:
            return f"Error reading existing file '{target}': {e}"

    # Overwrite mode ONLY if explicitly requested
    if overwrite_existing or not existing_content:
        final_content = code_to_add.strip() + "\n"
        action_msg = f"Overwrote '{target.name}' with new code"
    else:
        # Smart non-destructive integration
        # Check if existing content has an if __name__ == '__main__': block
        main_match = re.search(r"(\nif __name__\s*==\s*['\"]__main__['\"]\s*:)", existing_content)
        if main_match and ("def " in code_to_add or "class " in code_to_add):
            idx = main_match.start()
            final_content = (
                existing_content[:idx] +
                "\n\n" + code_to_add.strip() +
                "\n" + existing_content[idx:] + "\n"
            )
            action_msg = f"Neatly inserted new code before main block in '{target.name}', preserving existing code"
        else:
            final_content = (
                existing_content +
                "\n\n" +
                "# --- Added Code ---\n" +
                code_to_add.strip() + "\n"
            )
            action_msg = f"Neatly appended new code to '{target.name}', preserving existing code"

    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(final_content)

    opened_info = ""
    if open_in_editor and shutil.which("code"):
        try:
            subprocess.Popen(["code", str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            opened_info = " and opened in VS Code"
        except Exception:
            pass

    return f"{action_msg}{opened_info}. (File now has {len(final_content.splitlines())} lines)."

@tool
def write_code_to_file(
    code_content: str,
    file_path: Optional[str] = None,
    default_filename: str = "main.py",
    open_in_editor: bool = True
) -> str:
    """
    Intelligently write or append code. If user did not ask to modify an existing file,
    creates a separate file. If file exists, neatly appends without destroying existing code.
    """
    resolved_path, was_explicit = _resolve_file_path(file_path)

    # If user did NOT explicitly specify a file path, always create a separate file!
    if not was_explicit:
        # Generate appropriate filename from code or default
        return create_new_code_file(
            filename=default_filename,
            code_content=code_content,
            open_in_editor=open_in_editor
        )

    # User explicitly specified a file: use smart addition (non-destructive)
    return add_code_to_file(
        code_to_add=code_content,
        file_path=str(resolved_path),
        overwrite_existing=False,
        open_in_editor=open_in_editor
    )
