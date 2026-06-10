from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Memory:
    key: str
    content: str
    path: Path


class MemoryLoader:
    """Load and save persistent Markdown memories."""

    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = memory_dir
        self._last_mtime = 0.0
        self.memories: dict[str, Memory] = {}
        self.reload()

    def reload(self) -> None:
        if not self.memory_dir.exists():
            self.memories = {}
            self._last_mtime = 0.0
            return

        try:
            current_mtime = self.memory_dir.stat().st_mtime
        except Exception:
            current_mtime = 0.0

        if current_mtime <= self._last_mtime and self.memories:
            return

        new_memories: dict[str, Memory] = {}
        for path in self.memory_dir.glob("*.md"):
            try:
                text = path.read_text(encoding="utf-8")
                lines = text.splitlines()
                if not lines:
                    continue
                first_line = lines[0].strip()
                if first_line.startswith("#"):
                    key = first_line.lstrip("#").strip()
                else:
                    key = first_line

                body = "\n".join(lines[1:]).strip()
                new_memories[key] = Memory(key=key, content=body, path=path)
            except Exception:
                pass
        self.memories = new_memories
        self._last_mtime = current_mtime

    def descriptions(self) -> str:
        self.reload()
        if not self.memories:
            return "(no memories saved)"
        return "\n".join(f"- {key}" for key in self.memories.keys())

    def content(self, key: str) -> str:
        self.reload()
        memory = self.memories.get(key)
        if memory:
            return memory.content

        # Case-insensitive / whitespace-stripped fallback match
        norm_key = key.strip().lower()
        for k, m in self.memories.items():
            if k.strip().lower() == norm_key:
                return m.content

        return f"Error: Memory with key '{key}' not found."

    def save(self, key: str, content: str) -> Memory:
        key = key.strip()
        if not key:
            raise ValueError("Memory key must not be empty.")
        content = content.strip()
        if not content:
            raise ValueError("Memory content must not be empty.")

        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Overlay check for case-insensitive duplicate keys
        normalized_key = key.lower()
        target_key = key
        for existing_key in list(self.memories.keys()):
            if existing_key.lower() == normalized_key:
                target_key = existing_key
                break

        safe_name = hashlib.md5(target_key.encode("utf-8")).hexdigest() + ".md"
        path = self.memory_dir / safe_name

        # Skip redundant I/O if content hasn't changed
        if path.exists():
            try:
                old_text = path.read_text(encoding="utf-8")
                lines = old_text.splitlines()
                if len(lines) > 1 and "\n".join(lines[1:]).strip() == content:
                    memory = Memory(key=target_key, content=content, path=path)
                    self.memories[target_key] = memory
                    return memory
            except Exception:
                pass

        # Atomic safe write to avoid file corruption on termination/crash
        temp_path = path.with_suffix(".tmp")
        temp_path.write_text(f"# {target_key}\n{content}", encoding="utf-8")
        temp_path.rename(path)

        memory = Memory(key=target_key, content=content, path=path)
        self.memories[target_key] = memory

        try:
            self._last_mtime = self.memory_dir.stat().st_mtime
        except Exception:
            self._last_mtime = 0.0

        return memory
