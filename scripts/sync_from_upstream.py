#!/usr/bin/env python3
"""Sync the planning-only plugin from an upstream Superpowers checkout.

Usage:
  python3 scripts/sync_from_upstream.py /path/to/superpowers

If no source path is provided, the script uses the newest installed Codex
Superpowers plugin under ~/.codex/plugins/cache/openai-curated/superpowers/.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


SKILLS = ("brainstorming", "writing-plans", "executing-plans")
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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_source() -> Path:
    cache_root = Path.home() / ".codex/plugins/cache/openai-curated/superpowers"
    candidates = [path for path in cache_root.glob("*") if (path / "skills").is_dir()]
    if not candidates:
        raise SystemExit(
            "No upstream source provided and no Codex Superpowers cache found. "
            "Pass a source path explicitly."
        )
    return max(candidates, key=lambda path: path.stat().st_mtime)


def read_upstream_version(source: Path) -> str:
    manifest_path = source / ".codex-plugin/plugin.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        version = manifest.get("version")
        if isinstance(version, str) and version.strip():
            return version.strip()
    return "0.0.0"


def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected text not found in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def patch_planning_copy(plugin_root: Path) -> None:
    replace_required(
        plugin_root / "skills/brainstorming/SKILL.md",
        "docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md",
        "docs/planning/specs/YYYY-MM-DD-<topic>-design.md",
    )
    replace_required(
        plugin_root / "skills/brainstorming/spec-document-reviewer-prompt.md",
        "docs/superpowers/specs/",
        "docs/planning/specs/",
    )

    writing_plans = plugin_root / "skills/writing-plans/SKILL.md"
    replace_required(
        writing_plans,
        "**Context:** If working in an isolated worktree, it should have been created via the `superpowers:using-git-worktrees` skill at execution time.",
        "**Context:** This slim plugin does not manage worktrees. If an isolated branch or worktree is required, create it using normal project workflow before executing the plan.",
    )
    replace_required(
        writing_plans,
        "docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md",
        "docs/planning/plans/YYYY-MM-DD-<feature-name>.md",
    )
    replace_required(
        writing_plans,
        "> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.",
        "> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers-planning-only:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.",
    )
    replace_required(
        writing_plans,
        """**"Plan complete and saved to `docs/superpowers/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:executing-plans
- Batch execution with checkpoints for review
""",
        """**"Plan complete and saved to `docs/planning/plans/<filename>.md`. Two execution options:**

**1. Hand Off** - Keep the written plan as an implementation handoff for another session or engineer

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use `superpowers-planning-only:executing-plans`
- Batch execution with checkpoints for review
""",
    )
    replace_required(
        plugin_root / "skills/writing-plans/plan-document-reviewer-prompt.md",
        "Use this template when dispatching a plan document reviewer subagent.",
        "Use this template when reviewing a plan document in a separate review pass.",
    )

    executing_plans = plugin_root / "skills/executing-plans/SKILL.md"
    replace_required(
        executing_plans,
        "**Note:** Tell your human partner that Superpowers works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superpowers:subagent-driven-development instead of this skill.",
        "**Note:** This slim plugin intentionally executes plans inline. If you want subagent orchestration, use the full Superpowers plugin instead.",
    )
    replace_required(
        executing_plans,
        """After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice
""",
        """After all tasks complete and verified:
- Run the final verification commands from the plan.
- Summarize changed files, verification results, and any residual risks.
- Ask the user how they want to integrate the work if the plan did not already specify commit, merge, or PR steps.
""",
    )
    replace_required(
        executing_plans,
        "- Reference skills when plan says to",
        "- Reference only skills that are available in this slim plugin",
    )
    replace_required(
        executing_plans,
        """**Required workflow skills:**
- **superpowers:using-git-worktrees** - Ensures isolated workspace (creates one or verifies existing)
- **superpowers:writing-plans** - Creates the plan this skill executes
- **superpowers:finishing-a-development-branch** - Complete development after all tasks
""",
        """**Included planning skills:**
- **superpowers-planning-only:brainstorming** - Turns ideas into approved specs
- **superpowers-planning-only:writing-plans** - Creates the plan this skill executes
- **superpowers-planning-only:executing-plans** - Executes a written plan inline
""",
    )


def update_manifest(plugin_root: Path, upstream_version: str) -> None:
    manifest_path = plugin_root / ".codex-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = f"{upstream_version.split('+', 1)[0]}-planning.1"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def assert_clean_subset(plugin_root: Path) -> None:
    actual_skills = sorted(path.name for path in (plugin_root / "skills").iterdir() if path.is_dir())
    if actual_skills != sorted(SKILLS):
        raise SystemExit(f"Unexpected skills: {actual_skills}")

    offenders: list[str] = []
    for path in (plugin_root / "skills").rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                offenders.append(f"{path}: {pattern}")
    if offenders:
        raise SystemExit("Forbidden upstream references remain:\n" + "\n".join(offenders))


def main() -> None:
    root = repo_root()
    source = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else default_source()
    if not (source / "skills").is_dir():
        raise SystemExit(f"Upstream source does not look like Superpowers: {source}")

    plugin_root = root / "plugins/superpowers-planning-only"
    skills_root = plugin_root / "skills"
    if skills_root.exists():
        shutil.rmtree(skills_root)
    skills_root.mkdir(parents=True)

    for skill in SKILLS:
        shutil.copytree(source / "skills" / skill, skills_root / skill)

    assets_root = plugin_root / "assets"
    assets_root.mkdir(exist_ok=True)
    for asset in ("app-icon.png", "superpowers-small.svg"):
        shutil.copy2(source / "assets" / asset, assets_root / asset)
    shutil.copy2(source / "LICENSE", root / "LICENSE")
    shutil.copy2(source / "LICENSE", plugin_root / "LICENSE")

    upstream_version = read_upstream_version(source)
    patch_planning_copy(plugin_root)
    update_manifest(plugin_root, upstream_version)
    assert_clean_subset(plugin_root)
    print(f"Synced planning-only subset from {source} (upstream {upstream_version}).")


if __name__ == "__main__":
    main()
