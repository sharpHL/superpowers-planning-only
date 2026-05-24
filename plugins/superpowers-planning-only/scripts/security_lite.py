#!/usr/bin/env python3
"""Lightweight edit-time security checks for planning-only workflows."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


MAX_SCAN_CHARS = 200_000

BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "private-key",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "Private keys should not be written to the repository. Use a secret manager or local untracked file.",
    ),
    (
        "github-token",
        re.compile(r"\bgh[opsu]_[A-Za-z0-9_]{30,}\b"),
        "GitHub tokens should not be written to files. Use environment variables or GitHub secrets.",
    ),
    (
        "openai-style-key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
        "API keys should not be written to files. Use environment variables or a secret manager.",
    ),
    (
        "slack-token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
        "Slack tokens should not be written to files. Use environment variables or app secrets.",
    ),
    (
        "named-api-key",
        re.compile(
            r"(?i)\b(?:OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|GH_TOKEN)\s*=\s*['\"]?[^'\"\s]{12,}"
        ),
        "Named secret variables with concrete values should not be committed. Use .env.example placeholders instead.",
    ),
)

WARN_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "github-actions-workflow",
        (".github/workflows/",),
        "Review workflow edits for command injection. Put untrusted GitHub context values into env vars before using them in shell.",
    ),
    (
        "child-process-exec",
        ("child_process.exec", "exec(", "execSync("),
        "Shell execution can create command injection risk. Prefer execFile/spawn with argument arrays for dynamic values.",
    ),
    (
        "dynamic-code-execution",
        ("eval(", "new Function"),
        "Dynamic code execution can lead to injection vulnerabilities. Prefer parsers or explicit dispatch tables.",
    ),
    (
        "html-injection",
        ("dangerouslySetInnerHTML", ".innerHTML =", ".innerHTML=", "document.write"),
        "HTML injection can lead to XSS. Use textContent, safe DOM construction, or sanitized HTML.",
    ),
    (
        "python-unsafe-deserialization",
        ("pickle.load", "pickle.loads"),
        "Pickle can execute code when reading untrusted data. Prefer JSON or another safe serialization format.",
    ),
    (
        "python-shell",
        ("os.system", "from os import system"),
        "os.system should not receive dynamic values. Prefer subprocess.run with argument arrays.",
    ),
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


def first_dict(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def collect_strings(value: Any, result: list[str]) -> None:
    if len("".join(result)) > MAX_SCAN_CHARS:
        return
    if isinstance(value, str):
        result.append(value)
    elif isinstance(value, list):
        for item in value:
            collect_strings(item, result)
    elif isinstance(value, dict):
        for item in value.values():
            collect_strings(item, result)


def extract_tool_data(payload: dict[str, Any]) -> tuple[str, str, str]:
    tool_name = str(
        payload.get("tool_name")
        or payload.get("toolName")
        or payload.get("name")
        or payload.get("tool")
        or ""
    )
    tool_input = first_dict(
        payload.get("tool_input"),
        payload.get("toolInput"),
        payload.get("input"),
        payload.get("arguments"),
        payload.get("params"),
    )
    file_path = str(
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("filename")
        or tool_input.get("target")
        or ""
    )

    strings: list[str] = []
    if isinstance(tool_input.get("content"), str):
        strings.append(tool_input["content"])
    if isinstance(tool_input.get("new_string"), str):
        strings.append(tool_input["new_string"])
    if isinstance(tool_input.get("patch"), str):
        strings.append(tool_input["patch"])
    if isinstance(tool_input.get("edits"), list):
        collect_strings(tool_input["edits"], strings)
    if not strings:
        collect_strings(tool_input, strings)

    content = "\n".join(strings)[:MAX_SCAN_CHARS]
    return tool_name, file_path, content


def emit(message: str) -> None:
    print(message, file=sys.stderr)


def main() -> None:
    if sys.argv[1:] == ["--self-test"]:
        print("security-lite ok")
        return

    payload = read_payload()
    tool_name, file_path, content = extract_tool_data(payload)
    if not content and not file_path:
        return

    for rule_name, pattern, guidance in BLOCK_PATTERNS:
        if pattern.search(content):
            location = file_path or tool_name or "edit"
            emit(f"SECURITY-LITE BLOCK [{rule_name}] in {location}: {guidance}")
            sys.exit(2)

    warning_messages: list[str] = []
    normalized_path = file_path.replace("\\", "/")
    for rule_name, needles, guidance in WARN_RULES:
        haystacks = (normalized_path, content)
        if any(needle in haystack for needle in needles for haystack in haystacks):
            warning_messages.append(f"SECURITY-LITE WARNING [{rule_name}]: {guidance}")

    if warning_messages:
        emit("\n".join(dict.fromkeys(warning_messages)))


if __name__ == "__main__":
    main()
