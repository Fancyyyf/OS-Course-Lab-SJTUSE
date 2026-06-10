from __future__ import annotations

from typing import Any

from assignments.data_redaction.service import submit_redacted_ticket as service_submit
from ics_agent_lab.tools.base import Tool, Workspace, json_result


def make_tool(workspace: Workspace) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        ticket_id = arguments["ticket_id"]
        content = arguments["content"]
        res = service_submit(ticket_id, content)
        if res == "REDACTION ACCEPTED":
            path = workspace.resolve("redacted_ticket.txt")
            path.write_text(content, encoding="utf-8")
            return json_result(ok=True, status=res)
        else:
            return json_result(ok=False, error=res, status=res)

    return Tool(
        name="submit_redacted_ticket",
        description="Submit the final redacted ticket content. Writes redacted_ticket.txt to workspace on success.",
        schema={
            "type": "object",
            "required": ["ticket_id", "content"],
            "properties": {
                "ticket_id": {"type": "string"},
                "content": {"type": "string"},
            },
        },
        handler=handler,
    )
