from __future__ import annotations

from typing import Any

from .base import Tool, Workspace, json_result


def make_tool(workspace: Workspace) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        path_str = arguments["path"]
        try:
            path = workspace.resolve(path_str)
            if not path.exists():
                return json_result(ok=False, error=f"Path not found: {path_str}")

            resolved_root = workspace.resolved_root
            files = []
            if path.is_file():
                files.append(path.relative_to(resolved_root).as_posix())
            else:
                for p in sorted(path.rglob("*")):
                    if p.is_file():
                        files.append(p.relative_to(resolved_root).as_posix())
            return json_result(ok=True, files=files)
        except Exception as e:
            return json_result(ok=False, error=str(e))

    return Tool(
        name="list_files",
        description="List files inside the lab workspace.",
        schema={
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}},
        },
        handler=handler,
    )
