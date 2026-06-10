from __future__ import annotations

from typing import Any

from assignments.patch_review.service import read_patch_file as service_read_patch_file
from ics_agent_lab.tools.base import Tool, json_result


def make_tool() -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        path = arguments["path"]
        content = service_read_patch_file(path)
        if content is None:
            return json_result(
                ok=False, error=f"File '{path}' not found in patch fixtures."
            )
        return json_result(ok=True, content=content)

    return Tool(
        name="read_patch_file",
        description="Retrieve raw file content from patch fixtures.",
        schema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string"},
            },
        },
        handler=handler,
    )
