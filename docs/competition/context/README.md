# Prosperity 4 AI Context Pack (Round 4 active)

This folder contains a compact context pack for coding agents working on this
IMC Prosperity 4 repository. Currently configured for Round 4 ("The More The
Merrier", Salvinar). Round 3 facts are preserved as reference because the
algorithmic products and dynamics carry over.

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
- keep the numbered context files next to them or in a clearly referenced docs
  folder with paths updated accordingly

## Round 4 entry point

For a Round 4 session, after the four numbered context files, also read:
- `New Context/round_4_trading_round.md`: the official Round 4 wiki page.
- `New Context/round_4_aria_uplink.md`: the in-fiction uplink transcript.
- `New Context/round_4_hint_cards.md`: six prompt cards with research
  implications for IV / moneyness / volume / counterparty / vanilla-vs-exotic
  / chooser-options.

## Included source classes

- official competition docs
- narrative uplink summaries
- prompt-card strategic hints
- repo-local tooling / prompt-engineering context documents

## Quick routing

- Start with `00_PROSPERITY_CONTEXT_OVERVIEW.md`
- Then read exactly one specialized file based on task type
