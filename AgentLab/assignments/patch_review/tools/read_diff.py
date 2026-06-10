from __future__ import annotations

from typing import Any

from assignments.patch_review.service import read_diff as service_read_diff
from ics_agent_lab.tools.base import Tool, json_result


def make_tool() -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        diff = service_read_diff()
        return json_result(ok=True, diff=diff)

    return Tool(
        name="read_diff",
        description="Retrieve the pending patch diff.",
        schema={
            "type": "object",
            "properties": {},
        },
        handler=handler,
    )
