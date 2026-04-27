---
name: start-project
description: Read PROJECT.md from the repo root and treat its contents as the project brief — use this whenever the user says "start the project", "kick off the project", "build out PROJECT.md", or otherwise wants to begin implementing what PROJECT.md describes. Auto-invoke when the user references PROJECT.md as the source of truth for what to build.
---

## Steps

1. Read `PROJECT.md` from the repo root. If it's missing or empty, stop and tell the user — there's nothing to act on.

2. Treat the contents of `PROJECT.md` as the user's prompt. Restate your understanding of what's being built in 2-3 sentences so the user can confirm or correct before any code is written.

3. Ask 1-2 clarifying questions only if the brief is genuinely ambiguous on something load-bearing (scope, data model, auth model, deployment target). Skip this step if the brief is clear.

4. Propose an implementation approach broken into phases — each phase small enough to ship as a single PR. Wait for the user to greenlight the plan before coding.

5. Once approved, follow the project's standard workflow rules from `CLAUDE.md` (new branch, small PR per phase, tests for significant features). Auto-invoke other skills as the work demands them.

## Output

A short restatement of the brief, any clarifying questions, and a phased implementation plan ready for the user to approve.
