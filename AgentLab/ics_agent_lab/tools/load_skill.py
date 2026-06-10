from __future__ import annotations

from typing import Any

from ..skills import SkillLoader
from .base import Tool, json_result


def make_tool(skill_loader: SkillLoader | None) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        if skill_loader is None:
            return json_result(ok=False, error="Skill loader is not configured.")

        name = arguments["name"]
        content = skill_loader.content(name)
        if content.startswith("Error:"):
            return json_result(ok=False, error=content)
        return json_result(ok=True, content=content)

    return Tool(
        name="load_skill",
        description="Load the full body of a named skill from skills/<name>/SKILL.md.",
        schema={
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        handler=handler,
    )
