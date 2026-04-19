# Prosperity 4 Context Pack Overview

## Purpose

This pack is a compact, high-signal context layer for coding agents working on an
IMC Prosperity 4 repository. It is designed to be consumed by tools such as
Codex and Claude Code without wasting always-loaded context on details that are
only relevant for some tasks.

Use this pack to keep three things separate:

1. **Official competition facts**: rules, interfaces, products, limits, manual
   challenge mechanics.
2. **Soft strategic hints**: narrative prompt cards and uplink summaries that
   may contain useful clues but are not formal rules.
3. **Repo-local tooling reality**: backtesters, visualizer behavior, skills,
   agents, command surfaces, and caveats.

## Design principles

- Keep always-loaded entry files short.
- Put broad persistent rules in `AGENTS.md` / `CLAUDE.md`.
- Put task-specific detail in dedicated markdown files.
- Preserve source hierarchy and naming collisions explicitly.
- Preserve every materially useful fact, including “small” caveats that can
  change agent behavior.
- Prefer references and reading order over pasting huge blobs into every prompt.

## File map

- `AGENTS.md`
  - Thin Codex-facing entry file with durable repo rules.
- `CLAUDE.md`
  - Thin Claude Code entry file using `@` imports.
- `00_PROSPERITY_CONTEXT_OVERVIEW.md`
  - Shared trust model, cross-round facts, naming collisions, and file routing.
- `10_ALGO_TRADING_CONTEXT.md`
  - Algorithmic challenge facts and strategy-relevant hints for Rounds 1 and 2.
- `20_MANUAL_TRADING_CONTEXT.md`
  - Manual challenge facts for Round 1 auction and Round 2 investment game.
- `30_REPO_AND_TOOLING_CONTEXT.md`
  - Repo/tooling context extracted from uploaded repo-context docs.
- `README.md`
  - Human-facing summary of how to use the pack.

## Trust model and source hierarchy

When facts conflict, use this order:

1. **Official Prosperity written docs**
   - `Official Prosperity Context.md`
   - `Official Prosperity Context Round 1.md`
   - `Prosperity Round 2.md`
2. **Repo-context documents that describe local code/tooling**
   - `RUST_BACKTESTER_CONTEXT_FOR_AI_TOOLS.md`
   - `PYTHON_BACKTESTER_AND_VISUALIZER_CONTEXT_FOR_AI_TOOLS.md`
   - `CHATGPT_CONTEXT_FOR_CODEX_PROMPT_ENGINEERING.md`
3. **Narrative / transcript material**
   - `ARIA Uplink.md`
   - `Default_A.R.I.A Uplink_ Round 2.txt`
   - `ROUND1_PROMPT_HINTS_CONTEXT.md`

Practical rule:
- Treat official docs as authoritative for rules, interfaces, position limits,
  products, submission behavior, and round mechanics.
- Treat uplinks and prompt hints as clue-bearing but lower-authority.
- Treat repo-context docs as authoritative only for the local repo state they
  describe, not for live competition rules.

## Important naming collisions and canon choices

The uploaded materials are not perfectly aligned on world-building names.

Official written docs use:
- `Intara`
- `Intarian`
- `XIREN`
- `XIRECs`

Narrative uplink/transcript summaries use:
- `Entara`
- `Entarian`
- `Zyren`
- `Zyrex`

For agent work:
- use the **official written docs as canonical** for naming, rules, and
  competition facts
- treat the narrative variants as the same setting described through a lower-
  authority source

## What is actually verified in this sandbox

Verified directly in the sandbox:
- the uploaded markdown/txt files listed above

Not verified directly in the sandbox:
- the actual Prosperity repository tree mentioned by the repo-context files
- the code files those docs reference by path
- the presence of the described AGENTS files, skills, agents, datasets, or
  trader files on disk in this session

Therefore:
- repo/tooling statements in this pack are **derived from the uploaded
  repository-context documents**
- they should be treated as “documented repo reality” unless and until a real
  checkout is present and can be inspected directly

## Competition coverage in the uploaded materials

This pack covers:
- official general algorithm interface and exchange mechanics
- official Round 1
- official Round 2
- narrative Round 1 and Round 2 uplinks
- Round 1 prompt-card strategic hints
- repo-local backtester / visualizer / prompt-engineering context documents

This pack does **not** claim to cover later rounds beyond the fact that the
general official interface doc mentions that `bid()` is ignored outside Round 2.

## Cross-round competition facts that matter often

- The mission target in the uploaded official round docs is to reach a net PnL
  of **200,000 XIRECs or more** before the qualifying phase changes.
- Algorithmic and manual challenges are separate opportunities; manual results
  do not alter algorithmic mechanics and vice versa.
- Rounds last **72 hours** in the uploaded round docs/uplinks.
- Multiple submissions are allowed during a round, but the **last submitted
  program** is the one used for official evaluation of that round.
- The Round 1 and Round 2 algorithmic products in the uploaded official round
  docs are:
  - `ASH_COATED_OSMIUM`
  - `INTARIAN_PEPPER_ROOT`
- Position limits for both products in both uploaded round docs are:
  - `ASH_COATED_OSMIUM`: `80`
  - `INTARIAN_PEPPER_ROOT`: `80`

## General algorithm interface facts from official context

The official interface doc establishes these durable rules:

- Implement a `Trader` class with a `run(self, state)` method.
- For **Algorithmic Round 2**, the `Trader` class should also define
  `bid(self)`. It is fine to include `bid()` in all rounds; it is ignored
  outside Round 2.
- The official submission-compatible return shape is:
  `orders, conversions, traderData`
- The exchange/container is effectively stateless from call to call because the
  hosted container runs on AWS Lambda, so **do not rely on class or global
  variables persisting**.
- Use `traderData` for persistent state. The hosted environment truncates it at
  **50,000 characters**.
- Outstanding player quotes that are not traded on by bots are automatically
  canceled at the end of the iteration.
- Position-limit enforcement is worst-case on the aggregated buy/sell orders for
  a product in a single iteration: if the product would breach its limit if all
  those orders filled, the exchange rejects all orders for that product in that
  iteration.
- Official exchange execution is modeled as instantaneous relative to bots: if
  your order can match immediately, no faster bot gets in front of it.

## Routing rules for agents

If the task is about:
- algorithm design, signal mining, execution logic, submission compatibility, or
  Round 2 market-access bidding:
  - read `10_ALGO_TRADING_CONTEXT.md`
- manual challenge work, auction reasoning, or the Round 2 investment game:
  - read `20_MANUAL_TRADING_CONTEXT.md`
- backtesters, visualizer inputs, command choices, skills, local agents, or
  repo workflow:
  - read `30_REPO_AND_TOOLING_CONTEXT.md`

## What not to do

- Do not mix tutorial products such as `EMERALDS` or `TOMATOES` with live Round
  1 / Round 2 products unless the task explicitly targets tutorial data.
- Do not treat Round 1 narrative hints as stronger authority than official docs.
- Do not assume repo paths described in the uploaded repo-context files have
  been verified in the current sandbox.
- Do not treat local backtester behavior as official hosted truth when the docs
  explicitly call out mismatches.
