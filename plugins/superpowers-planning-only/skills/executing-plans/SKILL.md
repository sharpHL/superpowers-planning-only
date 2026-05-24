---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** This slim plugin intentionally executes plans inline. If you want subagent orchestration, use the full Superpowers plugin instead.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Run the final verification commands from the plan.
- Summarize changed files, verification results, and any residual risks.
- Ask the user how they want to integrate the work if the plan did not already specify commit, merge, or PR steps.

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference only skills that are available in this slim plugin
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Included planning skills:**
- **superpowers-planning-only:brainstorming** - Turns ideas into approved specs
- **superpowers-planning-only:writing-plans** - Creates the plan this skill executes
- **superpowers-planning-only:executing-plans** - Executes a written plan inline
