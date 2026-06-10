from __future__ import annotations

from typing import Any

from assignments.data_redaction.service import validate_redaction as service_validate
from ics_agent_lab.tools.base import Tool, json_result


def make_tool() -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        content = arguments["content"]
        issues = service_validate(content)
        return json_result(ok=True, issues=issues)

    return Tool(
        name="validate_redaction",
        description="Validate the redacted ticket content. Returns a list of issues (an empty list means validation passed).",
        schema={
            "type": "object",
            "required": ["content"],
            "properties": {
                "content": {"type": "string"},
            },
        },
        handler=handler,
    )
