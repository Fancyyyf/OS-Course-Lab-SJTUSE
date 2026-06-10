from __future__ import annotations

from typing import Any

from .base import Tool, Workspace, json_result


def make_tool(workspace: Workspace) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        path_str = arguments["path"]
        limit = arguments.get("limit")
        try:
            path = workspace.resolve(path_str)
            if not path.is_file():
                return json_result(
                    ok=False, error=f"File not found or is a directory: {path_str}"
                )
            content = path.read_text(encoding="utf-8")
            if limit is not None:
                lines = content.splitlines()
                if len(lines) > limit:
                    content = (
                        "\n".join(lines[:limit]) + f"\n... [truncated to {limit} lines]"
                    )
            return json_result(ok=True, content=content)
        except Exception as e:
            return json_result(ok=False, error=str(e))

    return Tool(
        name="read_file",
        description="Read a UTF-8 text file inside the lab workspace.",
        schema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
        handler=handler,
    )
