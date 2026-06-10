from __future__ import annotations

from typing import Any

from .base import Tool, Workspace, json_result


def make_tool(workspace: Workspace) -> Tool:

    def handler(arguments: dict[str, Any]) -> str:
        import subprocess

        command = arguments["command"]

        # Block dangerous commands
        unsafe_keywords = ["rm -rf /", "mkfs", "dd if="]
        for kw in unsafe_keywords:
            if kw in command:
                return json_result(
                    ok=False,
                    error=f"Command is blocked for safety reasons (contains '{kw}').",
                )

        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=workspace.resolved_root,
                capture_output=True,
                text=True,
                timeout=30.0,
            )
            return json_result(
                ok=True, stdout=res.stdout, stderr=res.stderr, exit_code=res.returncode
            )
        except subprocess.TimeoutExpired:
            return json_result(
                ok=False, error="Command execution timed out after 30 seconds."
            )
        except Exception as e:
            return json_result(ok=False, error=str(e))

    return Tool(
        name="bash",
        description="Run a shell command in the lab workspace with timeout and basic safety checks.",
        schema={
            "type": "object",
            "required": ["command"],
            "properties": {"command": {"type": "string"}},
        },
        handler=handler,
    )
