from __future__ import annotations

from typing import Any

from assignments.ephemeral_dispatch.service import (
    notify_user,
    read_dispatch_notice,
    request_dispatch_token,
)
from ics_agent_lab.tools.base import Tool, Workspace, json_result


def make_tool(workspace: Workspace) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        token = request_dispatch_token()
        notice = read_dispatch_notice(token)
        if notice is None:
            return json_result(ok=False, error="Token expired or invalid.")

        notify_status = notify_user(notice)

        path = workspace.resolve("dispatch_receipt.txt")
        path.write_text(notice, encoding="utf-8")

        return json_result(ok=True, notice=notice, notify_status=notify_status)

    return Tool(
        name="fetch_and_dispatch",
        description="Atomically request the ephemeral token, read the dispatch notice, notify the user, and write dispatch_receipt.txt.",
        schema={
            "type": "object",
            "properties": {},
        },
        handler=handler,
    )
