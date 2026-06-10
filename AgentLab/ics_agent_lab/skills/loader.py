from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
    path: Path


class SkillLoader:
    """Load skills from SKILL.md files under a directory."""

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.reload()

    def reload(self) -> None:
        self.skills: dict[str, Skill] = {}
        if not self.skills_dir.exists():
            return
        for path in self.skills_dir.glob("*/SKILL.md"):
            try:
                content = path.read_text(encoding="utf-8")
                lines = content.splitlines()
                if not lines or lines[0].strip() != "---":
                    continue

                fm_lines = []
                body_lines = []
                in_fm = True

                for line in lines[1:]:
                    if in_fm:
                        if line.strip() == "---":
                            in_fm = False
                        else:
                            fm_lines.append(line)
                    else:
                        body_lines.append(line)

                metadata = {}
                for line in fm_lines:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip()

                name = metadata.get("name")
                if name:
                    name = name.strip("'\"")
                description = metadata.get("description", "")
                if description:
                    description = description.strip("'\"")
                body = "\n".join(body_lines).strip()

                if name:
                    self.skills[name] = Skill(
                        name=name, description=description, body=body, path=path
                    )
            except Exception:
                pass

    def descriptions(self) -> str:
        self.reload()
        if not self.skills:
            return "(no skills available)"
        return "\n".join(f"- {s.name}: {s.description}" for s in self.skills.values())

    def content(self, name: str) -> str:
        self.reload()
        skill = self.skills.get(name)
        if skill:
            return skill.body
        return f"Error: Skill '{name}' not found."
