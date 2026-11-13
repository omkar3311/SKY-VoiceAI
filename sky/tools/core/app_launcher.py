import os
import shutil
import subprocess
from typing import Optional
from langchain_core.tools import tool

# Common application binary mappings
APP_MAP = {
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "code": "code",
    "chrome": "google-chrome",
    "google chrome": "google-chrome",
    "chromium": "chromium-browser",
    "firefox": "firefox",
    "browser": "google-chrome",
    "terminal": "gnome-terminal",
    "console": "gnome-terminal",
    "files": "nautilus",
    "file manager": "nautilus",
    "nautilus": "nautilus",
    "calculator": "gnome-calculator",
    "calc": "gnome-calculator",
    "settings": "gnome-control-center",
    "gedit": "gedit",
    "text editor": "gedit",
}

@tool
def open_application(app_name: str, target_path_or_url: Optional[str] = None) -> str:
    """
    Launch an application on the user's laptop (e.g. 'vs code', 'chrome', 'terminal', 'files', etc.).
    
    Args:
        app_name: Name of the application to open (e.g., 'vs code', 'chrome', 'firefox', 'terminal').
        target_path_or_url: Optional file path or web URL to open inside the application.
    """
    clean_name = app_name.strip().lower()
    binary = APP_MAP.get(clean_name, clean_name)
    
    # Check if executable exists
    resolved_bin = shutil.which(binary)
    if not resolved_bin:
        # Try finding with which
        if clean_name == "chrome":
            resolved_bin = shutil.which("google-chrome") or shutil.which("chromium")
        elif "code" in clean_name:
            resolved_bin = shutil.which("code")

    if not resolved_bin:
        return f"Error: Application '{app_name}' (binary '{binary}') is not found on this system."

    cmd = [resolved_bin]
    if target_path_or_url:
        cmd.append(os.path.expanduser(target_path_or_url))

    try:
        # Launch detached from current process
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        target_info = f" with '{target_path_or_url}'" if target_path_or_url else ""
        return f"Successfully opened '{app_name}' ({resolved_bin}){target_info}."
    except Exception as e:
        return f"Failed to launch '{app_name}': {str(e)}"

@tool
def close_application(app_name: str) -> str:
    """
    Gracefully terminate or kill a running application by name.
    
    Args:
        app_name: Name or process pattern of the application (e.g., 'code', 'chrome').
    """
    clean_name = app_name.strip().lower()
    binary = APP_MAP.get(clean_name, clean_name)
    
    try:
        result = subprocess.run(["pkill", "-f", binary], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Closed application '{app_name}'."
        else:
            return f"No running instance of '{app_name}' found to close."
    except Exception as e:
        return f"Error closing '{app_name}': {str(e)}"
