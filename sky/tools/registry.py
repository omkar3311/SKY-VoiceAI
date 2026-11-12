import ast
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Dict, List
from langchain_core.tools import BaseTool

from sky.config import DYNAMIC_TOOLS_DIR
from sky.tools.core.app_launcher import open_application, close_application
from sky.tools.core.file_ops import read_file, write_file, list_directory
from sky.tools.core.system_ops import (
    run_command,
    get_system_status,
    speak_to_user,
    stop_sky_assistant,
    put_pc_to_sleep,
    toggle_speech_output,
)
from sky.memory.store import remember_fact, recall_memory
from sky.tools.core.code_editor import (
    inspect_open_file_context,
    create_new_code_file,
    add_code_to_file,
    write_code_to_file,
)

CORE_TOOLS: List[BaseTool] = [
    open_application,
    close_application,
    read_file,
    write_file,
    list_directory,
    run_command,
    get_system_status,
    speak_to_user,
    stop_sky_assistant,
    put_pc_to_sleep,
    toggle_speech_output,
    remember_fact,
    recall_memory,
    inspect_open_file_context,
    create_new_code_file,
    add_code_to_file,
    write_code_to_file,
]

class ToolRegistry:
    """Manages core tools and dynamically generated tools."""

    def __init__(self, dynamic_dir: Path = DYNAMIC_TOOLS_DIR):
        self.dynamic_dir = dynamic_dir
        self.dynamic_dir.mkdir(parents=True, exist_ok=True)
        self._dynamic_tools: Dict[str, BaseTool] = {}
        self.reload_dynamic_tools()

    def get_core_tools(self) -> List[BaseTool]:
        return list(CORE_TOOLS)

    def reload_dynamic_tools(self) -> Dict[str, BaseTool]:
        """Scans dynamic_dir for python files and extracts BaseTool instances."""
        self._dynamic_tools.clear()
        
        for py_file in self.dynamic_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            module_name = f"sky.tools.dynamic.{py_file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = mod
                    spec.loader.exec_module(mod)
                    
                    # Extract any BaseTool instances
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if isinstance(attr, BaseTool):
                            self._dynamic_tools[attr.name] = attr
            except Exception as e:
                print(f"[ToolRegistry] Warning: Failed to load dynamic tool from {py_file}: {e}")
                
        return self._dynamic_tools

    def get_all_tools(self) -> List[BaseTool]:
        """Return combined list of core tools and dynamic tools."""
        all_tools = list(CORE_TOOLS)
        # Avoid duplicate names if any dynamic tool overrides
        dynamic_names = set(self._dynamic_tools.keys())
        all_tools = [t for t in all_tools if t.name not in dynamic_names]
        all_tools.extend(self._dynamic_tools.values())
        return all_tools

    def save_and_register_tool(self, tool_name: str, python_code: str) -> tuple[bool, str]:
        """
        Validates syntax, writes tool code to a .py file, and registers it.
        """
        # 1. Validate syntax with AST
        try:
            ast.parse(python_code)
        except SyntaxError as e:
            return False, f"Syntax Error in tool code: {str(e)} at line {e.lineno}"

        # Clean tool filename
        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in tool_name).lower()
        file_path = self.dynamic_dir / f"{clean_name}.py"

        # 2. Write file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(python_code)
        except Exception as e:
            return False, f"Failed to save tool file: {str(e)}"

        # 3. Import and load
        module_name = f"sky.tools.dynamic.{clean_name}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                return False, "Failed to create module spec for tool."
            
            mod = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)

            loaded_tools = []
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, BaseTool):
                    self._dynamic_tools[attr.name] = attr
                    loaded_tools.append(attr.name)

            if not loaded_tools:
                return False, f"File {file_path.name} was saved, but no LangChain @tool or BaseTool was found inside."

            return True, f"Successfully registered tool(s): {', '.join(loaded_tools)} from {file_path.name}"
        except Exception as e:
            return False, f"Error importing generated tool: {str(e)}"

    def get_summary(self) -> str:
        """Returns a string description of all currently available tools."""
        lines = []
        for t in self.get_all_tools():
            desc = (t.description or "").split("\n")[0].strip()
            lines.append(f"- {t.name}: {desc}")
        return "\n".join(lines)

# Singleton global registry instance
registry = ToolRegistry()
