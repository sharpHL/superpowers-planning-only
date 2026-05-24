#!/usr/bin/env python3
"""Static smoke tests for the planning-only plugin."""

from __future__ import annotations

import json
import sys
from pathlib import Path


EXPECTED_SKILLS = {"brainstorming", "writing-plans", "executing-plans"}
FORBIDDEN_PATTERNS = (
    "superpowers:",
    "docs/superpowers",
    "subagent-driven-development",
    "using-git-worktrees",
    "finishing-a-development-branch",
    "test-driven-development",
    "systematic-debugging",
    "requesting-code-review",
    "dispatching-parallel-agents",
    "verification-before-completion",
)
REQUIRED_PATTERNS = (
    "superpowers-planning-only:executing-plans",
    "docs/planning/specs/",
    "docs/planning/plans/",
)


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    repo = root()
    plugin_root = repo / "plugins/superpowers-planning-only"
    manifest_path = plugin_root / ".codex-plugin/plugin.json"
    claude_manifest_path = plugin_root / ".claude-plugin/plugin.json"
    marketplace_path = repo / ".agents/plugins/marketplace.json"
    claude_marketplace_path = repo / ".claude-plugin/marketplace.json"

    if not manifest_path.is_file():
        fail("missing Codex plugin manifest")
    if not claude_manifest_path.is_file():
        fail("missing Claude Code plugin manifest")
    if not marketplace_path.is_file():
        fail("missing Codex marketplace manifest")
    if not claude_marketplace_path.is_file():
        fail("missing Claude Code marketplace manifest")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != "superpowers-planning-only":
        fail("manifest name mismatch")
    if manifest.get("skills") != "./skills/":
        fail("manifest skills path mismatch")
    claude_manifest = json.loads(claude_manifest_path.read_text(encoding="utf-8"))
    if claude_manifest.get("name") != "superpowers-planning-only":
        fail("Claude Code manifest name mismatch")
    if claude_manifest.get("version") != manifest.get("version"):
        fail("manifest versions differ")

    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    if marketplace.get("name") != "superpowers-planning-only":
        fail("marketplace name mismatch")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        fail("marketplace should contain one plugin entry")
    entry = entries[0]
    if entry.get("name") != "superpowers-planning-only":
        fail("marketplace plugin name mismatch")
    if entry.get("source", {}).get("path") != "./plugins/superpowers-planning-only":
        fail("marketplace plugin path mismatch")

    claude_marketplace = json.loads(claude_marketplace_path.read_text(encoding="utf-8"))
    if claude_marketplace.get("name") != "superpowers-planning-only":
        fail("Claude Code marketplace name mismatch")
    claude_entries = claude_marketplace.get("plugins")
    if not isinstance(claude_entries, list) or len(claude_entries) != 1:
        fail("Claude Code marketplace should contain one plugin entry")
    claude_entry = claude_entries[0]
    if claude_entry.get("source") != "./plugins/superpowers-planning-only":
        fail("Claude Code marketplace plugin source mismatch")

    skills_root = plugin_root / "skills"
    actual_skills = {path.name for path in skills_root.iterdir() if path.is_dir()}
    if actual_skills != EXPECTED_SKILLS:
        fail(f"unexpected skills: {sorted(actual_skills)}")

    combined = ""
    for path in skills_root.rglob("*"):
        if path.is_file():
            combined += path.read_text(encoding="utf-8", errors="ignore")
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in combined:
            fail(f"forbidden full-Superpowers reference remains: {pattern}")
    for pattern in REQUIRED_PATTERNS:
        if pattern not in combined:
            fail(f"required planning-only reference missing: {pattern}")

    print("Planning-only plugin smoke tests passed.")


if __name__ == "__main__":
    main()
