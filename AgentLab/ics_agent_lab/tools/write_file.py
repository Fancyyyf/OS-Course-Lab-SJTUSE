from __future__ import annotations

from typing import Any

from .base import Tool, Workspace, json_result


def make_tool(workspace: Workspace) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        path_str = arguments["path"]
        content = arguments["content"]
        try:
            path = workspace.resolve(path_str)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return json_result(
                ok=True,
                message=f"Successfully wrote {len(content)} characters to {path_str}.",
            )
        except Exception as e:
            return json_result(ok=False, error=str(e))

    return Tool(
        name="write_file",
        description="Write a UTF-8 text file inside the lab workspace.",
        schema={
            "type": "object",
            "required": ["path", "content"],
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
        },
        handler=handler,
    )
