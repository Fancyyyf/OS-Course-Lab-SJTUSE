from __future__ import annotations

from typing import Any

from assignments.data_redaction.service import read_ticket as service_read
from ics_agent_lab.tools.base import Tool, json_result


def make_tool() -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        ticket_id = arguments["ticket_id"]
        res = service_read(ticket_id)
        if res is None:
            return json_result(ok=False, error=f"Ticket '{ticket_id}' not found.")
        return json_result(ok=True, content=res)

    return Tool(
        name="read_ticket",
        description="Read the raw text content of a ticket by ticket_id.",
        schema={
            "type": "object",
            "required": ["ticket_id"],
            "properties": {
                "ticket_id": {"type": "string"},
            },
        },
        handler=handler,
    )
