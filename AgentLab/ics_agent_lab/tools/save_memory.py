from __future__ import annotations

from typing import Any

from ..memory import MemoryLoader
from .base import Tool, json_result


def make_tool(memory_loader: MemoryLoader | None) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        if memory_loader is None:
            return json_result(ok=False, error="Memory loader is not configured.")

        key = arguments["key"]
        content = arguments["content"]
        try:
            memory_loader.save(key, content)
            return json_result(
                ok=True, message=f"Memory saved successfully under key: {key}"
            )
        except Exception as e:
            return json_result(ok=False, error=str(e))

    return Tool(
        name="save_memory",
        description=(
            "Save or replace one persistent Markdown memory. Use this only for "
            "stable facts, user preferences, or instructions that should survive "
            "future sessions."
        ),
        schema={
            "type": "object",
            "required": ["key", "content"],
            "properties": {
                "key": {"type": "string"},
                "content": {"type": "string"},
            },
        },
        handler=handler,
    )
