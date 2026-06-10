from __future__ import annotations

from typing import Any

from ..memory import MemoryLoader
from .base import Tool, json_result


def make_tool(memory_loader: MemoryLoader | None) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        if memory_loader is None:
            return json_result(ok=False, error="Memory loader is not configured.")

        key = arguments["key"]
        content = memory_loader.content(key)
        if content.startswith("Error:"):
            return json_result(ok=False, error=content)
        return json_result(ok=True, content=content)

    return Tool(
        name="read_memory",
        description="Read one persistent Markdown memory by exact key.",
        schema={
            "type": "object",
            "required": ["key"],
            "properties": {
                "key": {"type": "string"},
            },
        },
        handler=handler,
    )
