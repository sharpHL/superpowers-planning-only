#!/usr/bin/env python3
"""Write a small planning session summary on Stop hooks."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SIGNAL_RE = re.compile(
    r"\b(brainstorming|writing-plans|executing-plans|docs/planning|implementation plan|design doc)\b",
    re.IGNORECASE,
)


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            else:
                parts.append(flatten_text(item))
        return "\n".join(part for part in parts if part)
    if isinstance(value, dict):
        if "content" in value:
            return flatten_text(value["content"])
        if "text" in value:
            return str(value["text"])
    return ""


def read_transcript(path: str | None) -> list[tuple[str, str]]:
    if not path:
        return []
    transcript_path = Path(path)
    if not transcript_path.is_file():
        return []

    messages: list[tuple[str, str]] = []
    try:
        lines = transcript_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []

    for line in lines[-400:]:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = item.get("message") if isinstance(item, dict) else None
        if isinstance(message, dict):
            role = str(message.get("role") or item.get("role") or "")
            text = flatten_text(message.get("content"))
        elif isinstance(item, dict):
            role = str(item.get("role") or item.get("type") or "")
            text = flatten_text(item.get("content") or item.get("text"))
        else:
            continue
        if role and text.strip():
            messages.append((role, text.strip()))
    return messages


def run_git_status(cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
        )
    except Exception:
        return "Not available."
    output = result.stdout.strip()
    return output if output else "Clean or no tracked changes."


def list_planning_artifacts(cwd: Path) -> list[str]:
    root = cwd / "docs/planning"
    if not root.exists():
        return []
    files = [path for path in root.rglob("*") if path.is_file()]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [str(path.relative_to(cwd)) for path in files[:20]]


def short(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def summary_dir(cwd: Path) -> Path:
    preferred = cwd / ".superpowers-planning/summaries"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except OSError:
        fallback = Path.home() / ".superpowers-planning/summaries"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def main() -> None:
    if sys.argv[1:] == ["--self-test"]:
        print("planning-stop-summary ok")
        return
    if os.environ.get("SUPERPOWERS_PLANNING_SUMMARY", "1") == "0":
        return

    payload = read_payload()
    cwd = Path(str(payload.get("cwd") or os.environ.get("PWD") or os.getcwd())).resolve()
    transcript_path = payload.get("transcript_path") or payload.get("transcriptPath")
    session_id = str(payload.get("session_id") or payload.get("sessionId") or "unknown")
    messages = read_transcript(str(transcript_path) if transcript_path else None)
    artifacts = list_planning_artifacts(cwd)
    transcript_text = "\n".join(text for _, text in messages[-20:])
    should_write = bool(artifacts or SIGNAL_RE.search(transcript_text))
    if not should_write and os.environ.get("SUPERPOWERS_PLANNING_SUMMARY_ALWAYS") != "1":
        return

    last_user = next((text for role, text in reversed(messages) if role == "user"), "")
    last_assistant = next((text for role, text in reversed(messages) if role == "assistant"), "")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_session = re.sub(r"[^A-Za-z0-9_.-]+", "-", session_id)[:48] or "unknown"
    output_path = summary_dir(cwd) / f"{timestamp}-{safe_session}.md"

    artifact_lines = "\n".join(f"- `{artifact}`" for artifact in artifacts) or "- None found."
    status = run_git_status(cwd)
    missing_note = ""
    if SIGNAL_RE.search(transcript_text) and not artifacts:
        missing_note = "\n\nNote: Planning workflow language was detected, but no `docs/planning` artifacts were found."

    content = f"""# Planning Session Summary

**UTC:** {timestamp}
**CWD:** `{cwd}`
**Session:** `{session_id}`

## Last User Request

{short(last_user, 700) or "Not found."}

## Last Assistant Output

{short(last_assistant, 1200) or "Not found."}

## Planning Artifacts

{artifact_lines}

## Git Status

```text
{status}
```
{missing_note}
"""
    output_path.write_text(content, encoding="utf-8")
    print(f"Planning summary written: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
