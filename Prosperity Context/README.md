# Prosperity 4 AI Context Pack

This folder contains a compact context pack for coding agents working on an IMC
Prosperity 4 repository.

## Why this pack is structured this way

Current official guidance for both Codex and Claude Code favors:
- short root instruction files
- reusable repo guidance in `AGENTS.md` / `CLAUDE.md`
- task-specific detail in separate markdown files
- skills for optional or specialized workflows
- references/imports instead of bloated always-loaded instructions

Accordingly, this pack uses:
- thin root entry files: `AGENTS.md`, `CLAUDE.md`
- specialized task docs:
  - `00_PROSPERITY_CONTEXT_OVERVIEW.md`
  - `10_ALGO_TRADING_CONTEXT.md`
  - `20_MANUAL_TRADING_CONTEXT.md`
  - `30_REPO_AND_TOOLING_CONTEXT.md`

## Recommended placement

If you are using a real repo checkout:

- place `AGENTS.md` at the repo root for Codex
- place `CLAUDE.md` at the repo root for Claude Code
- keep the numbered context files next to them, or in a clearly referenced docs
  folder with paths updated accordingly

## Important limitation

The actual Prosperity repo is not present in this sandbox. The tooling/repo file
was derived from uploaded documentation that describes the repo, not from direct
inspection of the repo itself.

## Included source classes

- official competition docs
- narrative uplink summaries
- prompt-card strategic hints
- repo-local tooling / prompt-engineering context documents

## Quick routing

- Start with `00_PROSPERITY_CONTEXT_OVERVIEW.md`
- Then read exactly one specialized file based on task type
