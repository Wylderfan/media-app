# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Flask web app for media management. Just scaffolded from web-app-starter; no features built yet.

## Build Commands

```bash
# build: pip install -r requirements.txt
# test: pytest
```

## Code Style

- Use `snake_case` for naming
- Minimal comments — explain complex abstractions simply, not obvious logic
- Ask before introducing new frameworks or libraries
- Create basic tests when adding or modifying significant features

## Workflow Rules

- Always do a quick git pull to ensure we always have the latest commits
- Always create a new branch and PR for new work
- If working on an existing branch with an open PR, add a commit and update the PR with a comment
- Confirm a branch is merged before deleting it
- Keep PRs small and reviewable — divide large tasks into phases
- Before implementing anything non-trivial:
  1. Restate your understanding of the task
  2. Ask 1-2 clarifying questions for ambiguous requirements
  3. Propose the implementation approach before coding

## Development Approach

Balance thoroughness with efficiency — don't over-question simple tasks.
