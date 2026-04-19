# Repository and Tooling Context

## Scope and verification status

This file summarizes the repo/tooling reality described by the uploaded
repository-context documents.

Important limitation:
- the actual Prosperity repository checkout is **not present in this sandbox**
- therefore everything below is derived from the uploaded repo-context files and
  should be treated as **documented repo reality**, not directly re-verified
  file-system truth

Use this file when tasks involve:
- choosing a backtester
- selecting datasets or trader paths
- interpreting visualizer artifacts
- writing Codex / Claude Code guidance
- using repo-local skills or role agents

## Claimed repository shape from the uploaded docs

Repository root described in the docs:
- `/Users/tahakhan/Documents/Work/Projects/Prosperity`

Primary active workspace:
- `prosperity_rust_backtester/`

Other important described assets:
- repo-root `AGENTS.md`
- `prosperity_rust_backtester/AGENTS.md`
- repo-local skill under `.agents/skills/prosperity4-codex-skill/`
- project-local role definitions under `.codex/agents/`
- Python backtester under `imc-prosperity-4-backtester/`
- visualizer under `imc-prosperity-4-visualizer/`

## Canonical source split for agent work

The uploaded prompt-engineering repo doc makes these distinctions explicit:

### 1. AGENTS instruction files
These define routing, scope, repo rules, workflow, and ownership.
Agents should **follow** them rather than having their contents pasted into
prompts repeatedly.

### 2. Skills
The documented repo contains one reusable installable skill:
- `prosperity-4-strategy-engineer`

Use it for:
- strategy design
- trader improvement
- backtest diagnosis
- fair-value reasoning
- execution and inventory diagnosis
- safe adaptation of older ideas

### 3. Project-local role agents
The documented repo contains five project roles:
- `competition_research`
- `alpha_miner`
- `execution_risk`
- `strategy_engineer`
- `validator`

These are for **role-driven workflows**, not generic always-on skills.

### 4. Important documented gap
The uploaded repo prompt-engineering doc says the repo-root conceptual role set
mentions `repo_librarian`, but there is **no corresponding local agent file** in
`.codex/agents/`.

Implication:
- do not assume a runnable local `repo_librarian` exists

## Current best-practice implications for Codex and Claude Code

From current official docs:

### Codex / AGENTS.md
- Codex reads `AGENTS.md` files automatically before work.
- Guidance closer to the working directory overrides broader guidance.
- `AGENTS.md` should stay practical and concise.
- Good content includes repo layout, run/test commands, constraints, and what
  done means.
- If `AGENTS.md` gets large, keep it thin and point agents at more specific
  markdown files.

### Codex skills
- Skills use progressive disclosure: Codex begins from metadata and loads full
  `SKILL.md` only when relevant.
- Therefore task-specific or optional workflows are better as skills than as
  always-loaded AGENTS content.

### Claude Code / CLAUDE.md
- `CLAUDE.md` is read at the start of every session.
- It should stay short and human-readable.
- Put only broadly useful rules there.
- Use `@path` imports for linked docs rather than bloating the root file.
- Use skills for domain knowledge or workflows that are only relevant
  sometimes.

This context pack follows that model:
- thin entry files
- separate specialized markdown docs
- explicit routing by task type

## Documented active repo workflow

The uploaded repo docs strongly imply:
- active strategy work happens in `prosperity_rust_backtester/`
- tutorial work and round-specific work must be kept separate
- prompts should name:
  - target trader
  - dataset
  - baseline
  - relevant round/official context
- prompts should prefer one dominant change per iteration
- prompts should ask for a concrete validation step

## Rust backtester: documented repo-default local validator

The uploaded Rust tooling doc describes the Rust backtester as the **main local
validation engine** in the repo.

### Safe default rules

- Use the Rust backtester by default for local strategy validation.
- Pass an explicit trader path.
- Pass an explicit dataset or make target.
- Use `make tutorial` when you actually want tutorial behavior.
- Use persisted/full artifacts when diagnosis requires more than headline PnL.

### Documented repo caveats

#### Auto-picked trader is unsafe
The docs say:
- `traders/latest_trader.py` is referenced in docs but does not exist
- auto trader selection scans multiple directories and picks the most recently
  modified matching file
- because many work-in-progress trader variants exist, auto-pick is effectively
  unsafe / non-deterministic

#### `latest` dataset alias is not tutorial
The uploaded Rust tooling doc says:
- both `tutorial/` and `round1/` are populated
- `latest` resolves to `round1`, not tutorial

#### CSV observation gap
Documented limitation:
- CSV ingestion does **not** load `observations_round_*` CSV files

Implication:
- CSV-based local round datasets can have empty observations even if the hosted
  environment would expose them

#### Conversion gap
Documented limitation:
- conversions are recorded but not actually simulated in positions/cash by the
  Rust backtester

Implication:
- conversion-heavy strategies are not faithfully modeled locally

### Artifact model

Documented artifact modes:
- `none` -> `metrics.json`
- `submission` -> `metrics.json`, `submission.log`
- `diagnostic` -> `metrics.json`, `bundle.json`
- `full` -> `metrics.json`, `bundle.json`, `submission.log`, `activity.csv`,
  `pnl_by_product.csv`, `combined.log`, `trades.csv`

Important distinction:
- `submission.log` is official-payload-shaped JSON
- `combined.log` is logger-style plaintext and is better for rich visualizer
  inspection in single-run local analysis

### Local replay behavior that matters

The uploaded Rust tooling doc says:
- the engine builds a `TradingState`-like payload
- calls the Python trader
- captures stdout
- enforces position limits
- matches book depth first, then market trades
- marks inventory to mid for PnL
- accepts somewhat lenient local return shapes, but submission-compatible code
  should still return `(orders, conversions, traderData)`
- a Trader instance is reused across ticks within a run, but agents should still
  prefer `traderData` over hidden mutable state

## Python backtester and visualizer: documented secondary tools

The uploaded Python/visualizer doc describes these as secondary but still useful.

### Python backtester
Use when you specifically want:
- old `prosperity4bt` CLI behavior
- logger-style plaintext output
- `--vis` auto-open flow
- quick compatibility with the visualizer’s logger parser

Documented caveats:
- like the Rust engine, conversion requests are returned but not truly simulated
- local state still ought to use `traderData`
- unknown-product position limit fallback is `50`

### Visualizer
The visualizer supports **two parser families**:
1. official-style JSON payloads with `activitiesLog`
2. logger-style plaintext logs with `Sandbox logs:` and `Activities log:`

Implications:
- the same visualizer behaves differently depending on artifact shape
- official payloads are fine for prices/PnL/positions/trade markers
- official payloads do **not** reconstruct local intended orders or rich
  `traderData`
- logger-style logs are better when you want deep per-timestamp state

Documented safe rules:
- do **not** upload `.zip` bundles directly
- use extracted `.log` or `.json`
- use Rust `combined.log` for rich local inspection when available
- use Rust `submission.log` when official-style JSON is sufficient
- do not rely on stitched top-level multi-run bundle logs as primary visualizer
  inputs

## Prompting and workflow rules from uploaded repo docs

The uploaded ChatGPT/Codex repo doc repeatedly stresses:

- do not blur official round facts with local backtester behavior
- do not blur tutorial products with live round products
- prefer single-agent, single-dominant-change workflows by default
- only invoke the multi-role pipeline when explicitly needed
- only `strategy_engineer` should edit trader code in role-driven workflows
- non-code outputs should go under `prosperity-research/`
- older public Prosperity repos can be used for reusable ideas, but not as
  authority on current rules, products, syntax, or limits

## Practical working defaults for agents

For strategy work in the documented repo:
- work in `prosperity_rust_backtester/`
- name the trader path explicitly
- name the dataset explicitly
- name the baseline explicitly
- separate official facts from inferred assumptions
- preserve submission compatibility
- ask what the next backtest should confirm

For manual challenge work:
- keep algorithmic and manual contexts separate
- do not pretend backtester results answer the manual optimization problem

For prompt-engineering work:
- keep `AGENTS.md` / `CLAUDE.md` thin
- route richer detail to dedicated files
- use skills for optional workflows
- prefer path references/imports over pasting long instructions into every prompt

## One-paragraph handoff

The documented repo setup is a Rust-backtester-first Prosperity workspace with a
secondary Python backtester and a dual-parser visualizer. The most dangerous
mistakes for agents in this repo are using auto-picked traders, assuming
`latest` means tutorial, mixing tutorial and live Round 1 data, assuming
conversions are faithfully simulated, and confusing official-payload artifacts
with logger-style artifacts in the visualizer. Prompting should stay explicit
about target trader, dataset, baseline, and source hierarchy, while thin root
instruction files route agents to more detailed context only when needed.
