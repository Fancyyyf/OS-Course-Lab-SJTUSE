from __future__ import annotations

import concurrent.futures
import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..llm import LLMTransport, Message
from ..memory import MemoryLoader
from ..skills import SkillLoader
from ..tools import ToolRegistry
from .protocol import ManualJsonProtocol, ParseError
from .trace import TraceRecorder


@dataclass
class AgentConfig:
    max_parse_repairs: int = 2
    max_steps: int = 100
    compact_after_messages: int = 10
    compact_recent_messages: int = 3
    compact_summary_limit: int = 4000
    tool_result_limit: int = 6000
    compact_token_threshold: int = 2000
    max_compaction_calls: int = 3


class Agent:
    def __init__(
        self,
        llm: LLMTransport,
        tools: ToolRegistry,
        *,
        config: AgentConfig | None = None,
        protocol: ManualJsonProtocol | None = None,
        trace: TraceRecorder | None = None,
        skill_docs: str = "(no skills available)",
        memory_docs: str = "(no memory available)",
        name: str = "main",
        skill_loader: SkillLoader | None = None,
        memory_loader: MemoryLoader | None = None,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.config = config or AgentConfig()
        self.protocol = protocol or ManualJsonProtocol()
        self.trace = trace or TraceRecorder()
        self.skill_docs = skill_docs
        self.memory_docs = memory_docs
        self.name = name
        self.skill_loader = skill_loader
        self.memory_loader = memory_loader
        self._io_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self._dump_counter = 0
        self._dump_lock = threading.Lock()

    def _async_dump_long_text(self, text: str, step: int) -> str:
        with self._dump_lock:
            self._dump_counter += 1
            dump_id = self._dump_counter

        dump_dir = Path(".agent_memory/long_outputs")

        def write_task():
            dump_dir.mkdir(parents=True, exist_ok=True)
            dump_file = dump_dir / f"step_{step}_{dump_id}.txt"
            dump_file.write_text(text, encoding="utf-8")

        self._io_executor.submit(write_task)

        return f"[Too long ({len(text)} chars). Saved to .agent_memory/long_outputs/step_{step}_{dump_id}.txt. Use read_file/grep if needed.]"

    def save_trace(self, path: Path) -> None:
        self.trace.save_jsonl(path)

    def run(self, user_input: str) -> str:
        messages = self.new_session()
        return self.run_turn(messages, user_input)

    def estimate_messages_tokens(self, messages: list[Message]) -> int:
        return sum(
            max(1, (len(f"{msg['role']}: {msg['content']}") + 3) // 4)
            for msg in messages
        )

    def sanitize_tool_result(self, result: str) -> str:
        if not isinstance(result, str):
            return result
        result = result.replace("\r\n", "\n").replace("\r", "\n")
        result = result.replace("\t", "  ")
        lines = [line.rstrip() for line in result.splitlines()]
        result = "\n".join(lines)
        import re

        result = re.sub(r"\n\s*\n\s*\n+", "\n\n", result)
        return result.strip()

    def new_session(self) -> list[Message]:
        skill_docs = (
            self.skill_loader.descriptions() if self.skill_loader else self.skill_docs
        )
        memory_docs = (
            self.memory_loader.descriptions()
            if self.memory_loader
            else self.memory_docs
        )
        return [
            {
                "role": "system",
                "content": self.protocol.build_system_prompt(
                    self.tools.docs(compact=True), skill_docs, memory_docs
                ),
            }
        ]

    def run_turn(self, messages: list[Message], user_input: str) -> str:
        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        step = 1
        repair_attempts = 0
        llm_compaction_count = 0
        self._last_compact_step = -10

        while step <= self.config.max_steps:
            # 1. Context compaction check
            estimated_tokens = self.estimate_messages_tokens(messages)
            if (
                len(messages) > self.config.compact_after_messages
                or estimated_tokens > self.config.compact_token_threshold
            ):
                kept_recent = self.config.compact_recent_messages
                summarized_count = len(messages) - 1 - kept_recent

                # Rule-based zero-request truncation
                if summarized_count > 0:
                    modified = False
                    for i in range(1, len(messages) - kept_recent):
                        m = messages[i]
                        if m["role"] == "user" and len(m["content"]) > 2000:
                            m["content"] = self._async_dump_long_text(
                                m["content"], step
                            )
                            modified = True
                    if modified:
                        estimated_tokens = self.estimate_messages_tokens(messages)

                # If still over threshold, apply LLM compaction
                if (
                    len(messages) > self.config.compact_after_messages
                    or estimated_tokens > self.config.compact_token_threshold
                ):
                    # Ensure we have a minimum step gap to prevent infinite loops when recent messages are large
                    if (
                        step - self._last_compact_step > 3
                        and llm_compaction_count < self.config.max_compaction_calls
                    ):
                        if summarized_count > 0:
                            system_msg = messages[0]
                            recent_msgs = messages[-kept_recent:]
                            to_summarize = messages[1:-kept_recent]

                            transcript = []
                            for m in to_summarize:
                                role = m["role"]
                                content = m["content"]
                                if (
                                    role == "system"
                                    and "Summary of previous" in content
                                ):
                                    transcript.append(content)
                                else:
                                    # Pre-truncate long content for summary query
                                    if len(content) > 900:
                                        content = (
                                            content[:450]
                                            + "\n... [TRUNCATED FOR COMPACTION SUMMARY] ...\n"
                                            + content[-250:]
                                        )
                                    transcript.append(f"[{role.upper()}]:\n{content}")
                            to_summarize_str = "\n\n".join(transcript)

                            compaction_prompt = [
                                {
                                    "role": "system",
                                    "content": "Summarize history under 120 words. Preserve all exact details like names, keys, paths, credentials, and specific terms (e.g. 'path traversal', 'password reset') if present. Do not generalize them.",
                                },
                                {
                                    "role": "user",
                                    "content": to_summarize_str,
                                },
                            ]
                            try:
                                summary_text = self.llm.complete(compaction_prompt)
                                llm_compaction_count += 1
                                self._last_compact_step = step
                            except Exception as e:
                                summary_text = f"Failed to generate summary: {e}"

                            messages[:] = [
                                system_msg,
                                {
                                    "role": "system",
                                    "content": f"=== Summary of previous conversation steps ===\n{summary_text}\n",
                                },
                            ] + recent_msgs

                            self.trace.add(
                                step,
                                "context_compacted",
                                agent=self.name,
                                kept_recent=kept_recent,
                                summarized=summarized_count,
                            )

            # 2. LLM response
            try:
                raw_response = self.llm.complete(messages)
            except Exception as e:
                return f"LLM error: {e}"

            # 3. Log llm_response trace
            self.trace.add(step, "llm_response", agent=self.name, raw=raw_response)

            # 4. Parse response
            parsed = self.protocol.parse(raw_response)

            if isinstance(parsed, ParseError):
                self.trace.add(
                    step, "parse_error", agent=self.name, reason=parsed.reason
                )
                repair_attempts += 1
                if repair_attempts > self.config.max_parse_repairs:
                    messages.append({"role": "assistant", "content": raw_response})
                    err_msg = f"Agent stopped: model did not follow JSON protocol. Parse error: {parsed.reason}"
                    self.trace.add(step, "final", agent=self.name, content=err_msg)
                    return err_msg

                messages.append({"role": "assistant", "content": raw_response})
                repair_text = self.protocol.repair_prompt(raw_response, parsed.reason)
                messages.append({"role": "user", "content": repair_text})

            else:
                if repair_attempts > 0:
                    # Prune the failed attempts to save tokens and keep context clean
                    del messages[-2 * repair_attempts :]
                repair_attempts = 0

                if parsed.kind == "final":
                    self.trace.add(
                        step, "final", agent=self.name, content=parsed.content
                    )
                    messages.append({"role": "assistant", "content": raw_response})
                    return parsed.content or ""

                elif parsed.kind == "tool_call":
                    messages.append({"role": "assistant", "content": raw_response})

                    # Execute tool
                    tool_result = self.tools.run(parsed.name, parsed.arguments)
                    tool_result = self.sanitize_tool_result(tool_result)

                    # Log specific memory traces if applicable
                    if parsed.name == "save_memory":
                        self.trace.add(
                            step,
                            "memory_write",
                            agent=self.name,
                            id=parsed.arguments.get("key"),
                            kind="markdown",
                        )
                    elif parsed.name == "read_memory":
                        key = parsed.arguments.get("key")
                        self.trace.add(
                            step,
                            "memory_retrieve",
                            agent=self.name,
                            ids=[key] if key else [],
                            count=1 if key else 0,
                        )

                    # Truncate large tool result
                    if len(tool_result) > self.config.tool_result_limit:
                        tool_result = self._async_dump_long_text(tool_result, step)

                    # Log tool_call trace
                    self.trace.add(
                        step,
                        "tool_call",
                        agent=self.name,
                        name=parsed.name,
                        arguments=parsed.arguments,
                        result=tool_result,
                    )

                    # Append tool result
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Result of '{parsed.name}':\n{tool_result}",
                        }
                    )

            step += 1

        fallback_msg = (
            f"Agent stopped: reached maximum steps ({self.config.max_steps})."
        )
        self.trace.add(step, "final", agent=self.name, content=fallback_msg)
        return fallback_msg
