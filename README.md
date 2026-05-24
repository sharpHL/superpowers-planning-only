# Superpowers Planning Only

A slim Codex plugin derived from Superpowers 5.1.0. It keeps only the planning workflow:

- `brainstorming`
- `writing-plans`
- `executing-plans`

The full Superpowers plugin also includes TDD, debugging, code review, subagent orchestration, worktree management, and branch finishing workflows. Those are intentionally omitted here to reduce prompt surface area and keep the plugin focused on idea-to-plan work.

## Install In Codex

Add this repository as a marketplace:

```bash
codex plugin marketplace add https://github.com/sharpHL/superpowers-planning-only
```

Install the plugin:

```bash
codex plugin add superpowers-planning-only@superpowers-planning-only
```

Start a new Codex thread after installation so the new skills are loaded.

## Local Layout

```text
.agents/plugins/marketplace.json
plugins/superpowers-planning-only/
  .codex-plugin/plugin.json
  assets/
  skills/
    brainstorming/
    writing-plans/
    executing-plans/
```

## Attribution

This project is based on Superpowers by Jesse Vincent and retains the MIT license.
