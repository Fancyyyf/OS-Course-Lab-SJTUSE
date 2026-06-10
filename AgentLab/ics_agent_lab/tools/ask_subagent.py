from __future__ import annotations

from typing import Any, Callable

from .base import Tool, json_result


def make_tool(subagent_runner: Callable[[str], str] | None) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        if subagent_runner is None:
            return json_result(ok=False, error="Subagent is not configured.")

        task = arguments["task"]
        try:
            result = subagent_runner(task)
            return json_result(ok=True, content=result)
        except Exception as e:
            return json_result(ok=False, error=str(e))

    return Tool(
        name="ask_subagent",
        description="Ask a smaller subagent to solve a bounded text-only task.",
        schema={
            "type": "object",
            "required": ["task"],
            "properties": {"task": {"type": "string"}},
        },
        handler=handler,
    )
