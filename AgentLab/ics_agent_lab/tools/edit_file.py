from __future__ import annotations

from typing import Any

from .base import Tool, Workspace, json_result


def make_tool(workspace: Workspace) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        path_str = arguments["path"]
        old_text = arguments["old_text"]
        new_text = arguments["new_text"]
        try:
            path = workspace.resolve(path_str)
            if not path.is_file():
                return json_result(ok=False, error=f"File not found: {path_str}")
            content = path.read_text(encoding="utf-8")
            if old_text not in content:
                return json_result(ok=False, error=f"old_text not found in {path_str}")
            new_content = content.replace(old_text, new_text, 1)
            path.write_text(new_content, encoding="utf-8")
            return json_result(
                ok=True, message=f"Successfully replaced text in {path_str}."
            )
        except Exception as e:
            return json_result(ok=False, error=str(e))

    return Tool(
        name="edit_file",
        description="Replace the first exact text match in a UTF-8 file inside the lab workspace.",
        schema={
            "type": "object",
            "required": ["path", "old_text", "new_text"],
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string"},
                "new_text": {"type": "string"},
            },
        },
        handler=handler,
    )
