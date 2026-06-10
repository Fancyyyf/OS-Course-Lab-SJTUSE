from __future__ import annotations

from typing import Any

from assignments.patch_review.service import submit_review as service_submit_review
from ics_agent_lab.tools.base import Tool, Workspace, json_result


def make_tool(workspace: Workspace) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        verdict = arguments["verdict"]
        comments = arguments["comments"]
        res = service_submit_review(verdict, comments)
        if res == "REVIEW SUBMITTED":
            path = workspace.resolve("review.txt")
            path.write_text(
                f"Verdict: {verdict}\nComments: {comments}", encoding="utf-8"
            )
            return json_result(ok=True, status=res)
        else:
            return json_result(ok=False, error=res, status=res)

    return Tool(
        name="submit_review",
        description="Submit the review verdict and comments. Writes review.txt to workspace on success.",
        schema={
            "type": "object",
            "required": ["verdict", "comments"],
            "properties": {
                "verdict": {"type": "string"},
                "comments": {"type": "string"},
            },
        },
        handler=handler,
    )
