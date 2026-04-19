# ChatGPT Context For Engineering Codex Prompts In This Prosperity 4 Repository

## Purpose
This file is for **ChatGPT instances that are writing prompts for Codex**, not for Codex itself.

Its job is to help ChatGPT produce **repo-aware Codex prompts** that:
- use the right local instructions,
- reference the right skill or role when relevant,
- keep official Prosperity facts separate from local backtester evidence,
- avoid stale assumptions,
- ask for the right validation step.

ChatGPT should use this file to **write better Codex prompts**, not to solve the trading task directly unless the user explicitly asks for direct analysis.

---

## The Most Important Local Assets

### 1. Instruction files Codex should already read
- [`AGENTS.md`](/Users/tahakhan/Documents/Work/Projects/Prosperity/AGENTS.md)
- [`prosperity_rust_backtester/AGENTS.md`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/AGENTS.md)

ChatGPT should **reference** these files in prompts, not paste them into the prompt.

### 2. Official Prosperity context files in this repo
- [`Prosperity Context/Official Prosperity Context.md`](/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity%20Context/Official%20Prosperity%20Context.md)
- [`Prosperity Context/Official Prosperity Context Round 1.md`](/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity%20Context/Official%20Prosperity%20Context%20Round%201.md)

Use these when the prompt depends on:
- current official round products,
- syntax/interface requirements,
- current round mechanics,
- position limits,
- whether round-specific methods such as `bid()` matter.

### 3. Repo-local reusable skill
- Skill file: [`.agents/skills/prosperity4-codex-skill/SKILL.md`](/Users/tahakhan/Documents/Work/Projects/Prosperity/.agents/skills/prosperity4-codex-skill/SKILL.md)
- Skill name to mention in prompts: `prosperity-4-strategy-engineer`

This is the main reusable local skill ChatGPT should know about.

### 4. Project-scoped role agents in `.codex/agents`
These are **not installable skills**. They are project-local role definitions:
- [`competition_research.toml`](/Users/tahakhan/Documents/Work/Projects/Prosperity/.codex/agents/competition_research.toml)
- [`alpha_miner.toml`](/Users/tahakhan/Documents/Work/Projects/Prosperity/.codex/agents/alpha_miner.toml)
- [`execution_risk.toml`](/Users/tahakhan/Documents/Work/Projects/Prosperity/.codex/agents/execution_risk.toml)
- [`strategy_engineer.toml`](/Users/tahakhan/Documents/Work/Projects/Prosperity/.codex/agents/strategy_engineer.toml)
- [`validator.toml`](/Users/tahakhan/Documents/Work/Projects/Prosperity/.codex/agents/validator.toml)

These roles matter when ChatGPT is writing a prompt for a **multi-stage, role-driven Codex workflow**.

### 5. Active trading workspace
- [`prosperity_rust_backtester/`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester)
- [`prosperity_rust_backtester/traders/`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders)
- [`prosperity_rust_backtester/datasets/`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets)
- [`prosperity_rust_backtester/runs/`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs)
- [`Trader1/`](/Users/tahakhan/Documents/Work/Projects/Prosperity/Trader1) is legacy and should not be the default target.

---

## Critical Distinction ChatGPT Must Preserve

Do not blur these three things:

### A. Reusable skill
`prosperity-4-strategy-engineer` is a **skill**.

Use it in prompts when the user wants:
- strategy design,
- trader improvement,
- backtest diagnosis,
- fair-value reasoning,
- execution or inventory diagnosis,
- adaptation of ideas from older public Prosperity repos.

### B. Project-local role agents
The files in `.codex/agents/*.toml` are **project-local roles**, not reusable skills.

Use them in prompts only when the user wants a **role-based or multi-agent workflow**.

### C. AGENTS instruction files
The `AGENTS.md` files define repo routing, scope, guardrails, ownership, and workflow.

Prompts should tell Codex to follow them, not restate them at length.

---

## Current Repository Reality ChatGPT Should Know

### Active strategy work happens in `prosperity_rust_backtester/`
This is the main workspace for:
- local trader edits,
- backtesting,
- datasets,
- run artifacts.

### The repo currently contains one local installable skill
That skill is:
- `prosperity-4-strategy-engineer`

### The repo currently contains five local project agents
Those are:
- `competition_research`
- `alpha_miner`
- `execution_risk`
- `strategy_engineer`
- `validator`

### Important gap
The repo-root `AGENTS.md` mentions a `repo_librarian` role in the conceptual role set, but there is **no corresponding local file** under `.codex/agents/`.

ChatGPT should therefore:
- not assume a runnable local `repo_librarian` agent exists,
- only mention a repo-librarian-style step conceptually if the user explicitly wants public-repo mining.

---

## Official Context Versus Local Backtester Context

ChatGPT must explicitly distinguish:

### Official live-round context
Use the official context files when prompts are about the current competition round.

At the time of these repo files:
- the general official syntax/interface context is in `Official Prosperity Context.md`
- the current round-specific details are in `Official Prosperity Context Round 1.md`

Round 1 official products in that file are:
- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Round 1 official position limits in that file are:
- `ASH_COATED_OSMIUM`: 80
- `INTARIAN_PEPPER_ROOT`: 80

The file also mentions the manual **Exchange Auction** side task.

### Local backtester context
The local backtester workspace still includes tutorial datasets and round datasets:
- tutorial data exists under `prosperity_rust_backtester/datasets/tutorial/`
- Round 1 data exists under `prosperity_rust_backtester/datasets/round1/`

Tutorial products are different from Round 1 products.

ChatGPT must never write prompts that casually mix:
- tutorial `EMERALDS` / `TOMATOES`
- Round 1 `ASH_COATED_OSMIUM` / `INTARIAN_PEPPER_ROOT`

Every Codex prompt should make the target context explicit:
- tutorial iteration,
- round-specific analysis,
- round-specific implementation,
- general submission-compatibility review.

---

## Source Hierarchy ChatGPT Must Preserve

When writing prompts for Codex, preserve this order:

1. Official Prosperity files and syntax/interface material for current facts.
2. This repository's current files, datasets, backtester behavior, and run artifacts.
3. Older public Prosperity repos only for reusable ideas about strategy, architecture, and diagnostics.

Prompts must never encourage Codex to treat older public repos as authority for:
- current round products,
- current round rules,
- hidden mechanics,
- current syntax requirements,
- current position limits.

---

## How ChatGPT Should Integrate The Local Skill Into Prompts

For strategy-oriented tasks, ChatGPT should usually include a line like:

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-strategy-engineer` skill.
```

That prompt should usually ask Codex to:
- separate official facts from inferred assumptions,
- classify the relevant products by market type,
- state the fair-value hypothesis,
- identify the dominant failure mode,
- choose the smallest defensible change,
- preserve submission compatibility,
- say what the next backtest should confirm.

This skill is especially relevant for:
- new trader variants,
- poor PnL diagnosis,
- inventory problems,
- adapting older ideas safely,
- deciding between a small patch and a broader redesign.

ChatGPT does **not** need to mention this skill for purely mechanical tasks such as:
- renaming files,
- updating docs,
- cleaning a CSV path,
- moving run artifacts.

---

## How ChatGPT Should Integrate The Project Roles Into Prompts

Only do this when the user actually wants:
- multi-stage research,
- role-based analysis,
- a full research-to-implementation pipeline,
- explicit division of responsibility.

### Role order to reference
For role-based prompts, use this order:
1. `competition_research`
2. `alpha_miner`
3. `execution_risk`
4. `strategy_engineer`
5. `validator`

If public-repo mining is explicitly required, ChatGPT may mention a conceptual repo-librarian step after `competition_research`, but should not assume a local `.codex/agents/repo_librarian.toml` exists.

### Role responsibilities
Use this mapping in prompts:

- `competition_research`
  Verifies official current facts, flags stale assumptions, separates official from inferred, and writes to `prosperity-research/01_assumptions/current_assumptions.md`.

- `alpha_miner`
  Analyzes local datasets and run artifacts, slices regimes, ranks candidate edges, and writes to `prosperity-research/04_signal_notes/latest_signal_ranking.md`.

- `execution_risk`
  Diagnoses fill realism, inventory path, drawdowns, counterfactual quote quality, and writes to `prosperity-research/05_execution_risk/latest_execution_risk_report.md`.

- `strategy_engineer`
  Is the default implementation owner. Only this role should edit trader code under `prosperity_rust_backtester/traders/`.

- `validator`
  Compares a named candidate against a named baseline, runs backtests, inspects artifacts, and ends with a SHIP or REJECT decision in `prosperity-research/06_validation/latest_validation_report.md`.

### Role guardrails ChatGPT should preserve
Prompts should preserve these boundaries:
- only `strategy_engineer` edits trader code by default,
- non-code roles write into `prosperity-research/`,
- `validator` should not approve without a named baseline,
- `Trader1/` remains reference-only,
- one strategy iteration should center on one dominant change.

---

## Prompting Defaults ChatGPT Should Encourage

Unless the user explicitly wants something else, prompt Codex to:
- work in `prosperity_rust_backtester/`,
- follow both `AGENTS.md` files,
- create a new trader variant instead of overwriting a strong baseline,
- keep the change narrow and attributable,
- backtest locally,
- inspect more than headline PnL,
- state the expected effect on PnL, inventory, or execution quality.

For a typical strategy prompt, ChatGPT should specify:
- target trader file,
- target dataset or round,
- comparison baseline,
- whether a new variant should be created,
- the validation command to run,
- what outcome should improve.

---

## Validation And Command Surface ChatGPT Should Reference

The preferred local surface is the backtester workspace:
- [`prosperity_rust_backtester/README.md`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/README.md)
- [`prosperity_rust_backtester/Makefile`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/Makefile)

Useful prompt language:

```text
Backtest locally using the Makefile workflow and report the exact command used.
```

Typical examples ChatGPT can mention in prompts:

```bash
make tutorial TRADER=traders/latest_trader.py
make tutorial TRADER=traders/latest_trader.py DAY=-1
make tutorial TRADER=traders/latest_trader.py PERSIST=1
make backtest TRADER=traders/latest_trader.py
```

When prompting for validation, ask Codex to inspect:
- total PnL,
- per-day PnL,
- product-level contribution,
- inventory behavior,
- time spent near position limits,
- obvious adverse passive fills,
- relevant run artifacts such as `metrics.json` when persisted.

---

## Prompt Anti-Patterns ChatGPT Should Avoid

Do not write vague prompts like:
- "make the trader better"
- "find alpha"
- "use all the agents"

Do not write prompts that:
- fail to name the target trader,
- fail to name the dataset,
- blur tutorial and Round 1 products,
- assume public old repos are authoritative,
- ask non-code roles to edit trader code,
- ask `validator` to approve without a baseline,
- tell Codex to overwrite the best current trader without reason,
- encourage broad rewrites before diagnosing the dominant bottleneck.

---

## Recommended Prompt Shapes

### 1. Single-agent strategy improvement
Use this by default.

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-strategy-engineer` skill.

Work in `prosperity_rust_backtester/`.

Goal:
Improve <trader file> on <dataset/round> while preserving submission compatibility.

Context:
- target trader: <path>
- baseline: <path>
- dataset: <tutorial / round1 / specific day>
- relevant official context: <file if round-specific>
- current issue: <brief problem statement>

Constraints:
- prefer one dominant strategic change
- create a new trader variant unless overwriting is explicitly requested
- do not touch `Trader1/`
- separate official facts from inferred assumptions

Done when:
- the code change is localized and attributable
- the exact backtest command is run or stated
- the expected effect is explained
- the next validation signal is identified
```

### 2. Multi-stage role-driven prompt
Use only when the user explicitly wants a role-based workflow.

```text
Use the repo's AGENTS.md guidance. Treat this as a role-driven Prosperity workflow.

Order of work:
1. `competition_research` verifies official current facts from the repo's official context files.
2. `alpha_miner` analyzes the local datasets and existing run artifacts for the named products and trader.
3. `execution_risk` diagnoses fill realism, inventory path, and drawdown behavior.
4. `strategy_engineer` implements the single best next change in `prosperity_rust_backtester/traders/`.
5. `validator` compares the candidate against the named baseline and ends with SHIP or REJECT.

Task:
<clear task>

Constraints:
- only `strategy_engineer` edits trader code
- non-code outputs go under `prosperity-research/`
- use the `prosperity-4-strategy-engineer` skill when strategy reasoning is needed
- keep one dominant change per iteration
```

### 3. Official-fact-first prompt
Use this when the user is talking about a live round, a syntax requirement, or uncertainty about products/mechanics.

```text
Before making any code change, verify the relevant official facts from:
- `Prosperity Context/Official Prosperity Context.md`
- `Prosperity Context/Official Prosperity Context Round 1.md`

Separate official facts from inferred assumptions, then proceed with the smallest valid implementation or analysis step.
Use the repo's AGENTS.md guidance and the `prosperity-4-strategy-engineer` skill.
```

### 4. Backtest-diagnosis prompt
Use this when the user provides weak results, logs, or artifacts.

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-strategy-engineer` skill.

Inspect the named trader, dataset, and run artifacts together.
Identify the dominant failure mode first: fair value, taking thresholds, passive fills, inventory control, or state handling.
Implement only the smallest follow-up change that attacks that failure mode, then state the exact backtest command and what metric should move if the diagnosis is correct.
```

---

## What ChatGPT Should Usually Return To The User

When the user asks ChatGPT to generate a Codex prompt, ChatGPT should usually return:

1. one short note on what the prompt is optimized for,
2. one polished prompt in a code block,
3. optionally one stronger alternative for a multi-stage or role-based workflow.

The prompt should usually be written in direct imperative language to Codex.

---

## Bottom Line

If ChatGPT remembers only a few rules, they should be these:

1. Tell Codex to follow the repo `AGENTS.md` files instead of pasting them.
2. Use `prosperity-4-strategy-engineer` for strategy reasoning tasks.
3. Treat `.codex/agents/*.toml` as project roles, not installable skills.
4. Be explicit about whether the task is tutorial work or live Round 1 work.
5. Preserve the official-vs-local-vs-public-repo source hierarchy.
6. Ask for one dominant change, a concrete backtest step, and a named baseline.
