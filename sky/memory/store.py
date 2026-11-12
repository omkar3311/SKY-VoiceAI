import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from langchain_core.tools import tool
from sky.config import PROJECT_ROOT

MEMORY_FILE = PROJECT_ROOT / "sky" / "memory" / "memory.json"

DEFAULT_MEMORY = {
    "user_profile": {
        "name": "Omkar Waghmare",
        "creator": "Omkar Waghmare",
        "role": "Developer and Creator of Sky AI"
    },
    "facts": [
        {
            "fact": "Sky was designed and developed by Omkar Waghmare.",
            "category": "creator",
            "date": "2026-11-01"
        }
    ],
    "recent_interactions": []
}

class MemoryStore:
    """Manages persistent long-term memory for Sky AI."""

    def __init__(self, file_path: Path = MEMORY_FILE):
        self.file_path = file_path
        self._ensure_storage()

    def _ensure_storage(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save_raw(DEFAULT_MEMORY)

    def _load_raw(self) -> dict:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return dict(DEFAULT_MEMORY)

    def _save_raw(self, data: dict):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[MemoryStore] Error saving memory: {e}")

    def add_fact(self, fact: str, category: str = "user_preference") -> str:
        """Stores a new fact or preference into long-term memory."""
        data = self._load_raw()
        entry = {
            "fact": fact.strip(),
            "category": category.strip().lower(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        # Prevent exact duplicates
        for existing in data.get("facts", []):
            if existing.get("fact", "").lower() == fact.strip().lower():
                return f"I already remember that: '{fact}'."

        data.setdefault("facts", []).append(entry)
        self._save_raw(data)
        return f"Successfully saved to memory: '{fact}'."

    def search_facts(self, query: Optional[str] = None) -> List[str]:
        """Search or return all remembered facts."""
        data = self._load_raw()
        facts = data.get("facts", [])
        if not query:
            return [f"• {item['fact']} ({item.get('category', 'general')})" for item in facts]

        q = query.lower()
        matched = []
        for item in facts:
            if q in item.get("fact", "").lower() or q in item.get("category", "").lower():
                matched.append(f"• {item['fact']}")
        return matched

    def log_interaction(self, task: str, summary: str):
        """Record completed task into interaction history."""
        data = self._load_raw()
        history = data.setdefault("recent_interactions", [])
        history.append({
            "task": task[:120],
            "summary": summary[:200],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        # Keep latest 15 interactions
        data["recent_interactions"] = history[-15:]
        self._save_raw(data)

    def get_memory_context_prompt(self) -> str:
        """Generates a condensed memory context string for system prompt injection."""
        data = self._load_raw()
        profile = data.get("user_profile", {})
        facts = data.get("facts", [])
        recent = data.get("recent_interactions", [])

        lines = [
            f"User: {profile.get('name', 'Omkar Waghmare')} (Creator & Developer of Sky AI)",
            "Known facts & preferences:"
        ]
        for f in facts[-8:]:  # Show recent 8 facts
            lines.append(f"  - {f['fact']}")

        if recent:
            lines.append("Recent tasks completed:")
            for r in recent[-3:]:
                lines.append(f"  - {r['task']} (Done)")

        return "\n".join(lines)

memory_store = MemoryStore()

@tool
def remember_fact(fact: str, category: str = "preference") -> str:
    """
    Save an important fact, user preference, project detail, or piece of knowledge
    into Sky's permanent long-term memory so it is remembered across sessions and restarts.
    
    Args:
        fact: The piece of information to permanently remember (e.g. 'Omkar prefers Python 3.12', 'Omkar's favorite framework is FastAPI').
        category: Category tag (e.g. 'preference', 'project', 'tool', 'personal').
    """
    return memory_store.add_fact(fact=fact, category=category)

@tool
def recall_memory(topic: Optional[str] = None) -> str:
    """
    Look up stored memories, facts, preferences, or past tasks from Sky's long-term memory.
    
    Args:
        topic: Keyword or topic to search for (e.g. 'creator', 'preferences', 'python'). If omitted, lists key memories.
    """
    results = memory_store.search_facts(topic)
    if not results:
        return f"No memories found matching '{topic}'."
    return "Remembered facts:\n" + "\n".join(results)
