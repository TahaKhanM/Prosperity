# ChatGPT Context For Engineering Codex Prompts In This Prosperity 4 Repository

## Purpose
This file is for **ChatGPT instances that are writing prompts for Codex**, not for Codex itself.

Its job is to help ChatGPT produce **repo-aware Codex prompts** that:
- use the right local instructions,
- reference the right local skill or role when relevant,
- keep official Prosperity facts separate from local backtester evidence,
- avoid stale Round 1 assumptions when the active workflow is now Round 2,
- use the shared alpha registry so the alpha-finder and strategy-builder chats do not duplicate work,
- ask for the right validation step and artifact updates.

ChatGPT should use this file to **write better Codex prompts**, not to solve the trading task directly unless the user explicitly asks for direct analysis.

---

## The Most Important Local Assets

### 1. Instruction files Codex should already read
- `AGENTS.md`
- `prosperity_rust_backtester/AGENTS.md`

ChatGPT should **reference** these files in prompts, not paste them into the prompt.

### 2. Official Prosperity context files in this repo
Use the official context files when the prompt depends on:
- current official round products,
- syntax/interface requirements,
- current round mechanics,
- position limits,
- whether round-specific methods such as `bid()` matter,
- manual-round mechanics that must stay separate from the algo trader.

Most relevant files now include:
- `Prosperity Context/Official Prosperity Context.md`
- `Prosperity Context/Official Prosperity Context Round 1.md`
- `Prosperity Context/Prosperity Round 2.md`
- `Prosperity Context/ARIA Uplink.md`
- `Prosperity Context/Default_A.R.I.A Uplink_ Round 2.txt`
- `Prosperity Context/ROUND1_PROMPT_HINTS_CONTEXT.md`

### 3. Repo-local reusable skills in `.agents/skills`
These are **installable local skills** and should be referenced by name when relevant.

#### A. Strategy-builder skill
- Skill file: `.agents/skills/prosperity4-codex-skill/SKILL.md`
- Skill name: `prosperity-4-strategy-engineer`

Use this for the dedicated **Round 2 strategy-builder chat**.
It owns:
- turning ranked Round 2 alphas into trader changes,
- keeping submission compatibility,
- preserving one dominant change per iteration,
- updating the shared Round 2 alpha registry with ideas it becomes aware of while implementing.

#### B. Alpha-finder skill
- Skill file: `.agents/skills/prosperity4-round2-alpha-finder/SKILL.md`
- Skill name: `prosperity-4-round2-alpha-finder`

Use this for the dedicated **Round 2 alpha-finding chat**.
It owns:
- product classification,
- regime slicing,
- alpha discovery,
- evidence ranking,
- deduplicated maintenance of the shared Round 2 alpha registry,
- writing ranked outputs without editing trader code.

#### C. Log-analysis skill
- Skill file: `.agents/skills/prosperity4-round2-log-analyst/SKILL.md`
- Skill name: `prosperity-4-round2-log-analyst`

Use this for the dedicated **Round 2 log-analysis / diagnosis chat**.
It owns:
- official-log and local-run-artifact diagnosis,
- dominant-failure-mode naming,
- diagnosis-packet generation,
- targeted alpha-registry updates only when logs clearly confirm, falsify, or merge alpha ideas.

#### D. Full-workflow skill
- Skill file: `.agents/skills/prosperity4-round2-autopilot/SKILL.md`
- Skill name: `prosperity-4-round2-autopilot`

Use this only when the user explicitly wants **one chat to do the full Round 2 loop**:
- refresh the alpha picture,
- choose one high-value target,
- implement one change,
- inspect evidence,
- update the alpha registry,
- end with the next step.

### 4. Project-scoped role agents in `.codex/agents`
These are **project-local role definitions**, not installable skills.

Current local agents are:
- `.codex/agents/competition_research.toml`
- `.codex/agents/alpha_miner.toml`
- `.codex/agents/execution_risk.toml`
- `.codex/agents/log_analyst.toml`
- `.codex/agents/strategy_engineer.toml`
- `.codex/agents/validator.toml`
- `.codex/agents/round2_autopilot.toml`

These roles matter when ChatGPT is writing a prompt for a **role-driven Codex workflow**.

### 5. Shared alpha registry
This is the coordination layer between the alpha-finder and strategy-builder chats.

Registry path:
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`

ChatGPT should treat this file as mandatory context whenever the task is about:
- Round 2 alpha discovery,
- Round 2 implementation,
- Round 2 validation,
- Round 2 diagnosis,
- avoiding duplicate idea generation.

### 6. Active research and trading workspace
The active workspace is now split cleanly:

#### Research / analysis layer
- `prosperity-research/`
- `prosperity-research/01_assumptions/`
- `prosperity-research/03_eda/round1/`
- `prosperity-research/04_signal_notes/`
- `prosperity-research/05_execution_risk/`
- `prosperity-research/06_validation/`
- `prosperity-research/07_manual_round/`
- `prosperity-research/08_playbooks/`

#### Active implementation / backtesting layer
- `prosperity_rust_backtester/`
- `prosperity_rust_backtester/traders/`
- `prosperity_rust_backtester/datasets/`
- `prosperity_rust_backtester/runs/`

#### Legacy area
- `Trader1/` is legacy and should not be the default target.

---

## Critical Distinctions ChatGPT Must Preserve

Do not blur these four things:

### A. Reusable skills
The `.agents/skills/*/SKILL.md` files define **installable local skills**.

Use them when the user wants a specific chat mode such as:
- Round 2 alpha finding,
- Round 2 strategy building,
- Round 2 log analysis,
- one-chat Round 2 autopilot.

### B. Project-local role agents
The `.codex/agents/*.toml` files are **project-local role definitions**, not reusable skills.

Use them only when the user wants a **role-based or multi-agent workflow**.

### C. AGENTS instruction files
The `AGENTS.md` files define repo routing, scope, guardrails, ownership, and workflow.

Prompts should tell Codex to follow them, not restate them at length.

### D. Shared alpha registry
`prosperity-research/04_signal_notes/round2_alpha_registry.md` is the shared Round 2 memory layer.

ChatGPT should preserve this rule:
- the alpha-finder chat should read and update it,
- the strategy-builder chat should read and update it,
- the log-analysis and validation flows should update it only when evidence clearly changes alpha status,
- prompts should not encourage duplicative alpha generation outside the registry.

---

## Current Repository Reality ChatGPT Should Know

### 1. Active strategy work still happens in `prosperity_rust_backtester/`
This is the main workspace for:
- local trader edits,
- backtesting,
- datasets,
- run artifacts,
- validation.

### 2. The active research and analysis layer now lives in `prosperity-research/`
This is where non-code outputs should go by default, including:
- assumptions,
- EDA outputs,
- alpha notes,
- execution-risk reports,
- validation reports,
- manual-round notes,
- prompt libraries and runbooks.

### 3. The repository now has four local installable skills
Those are:
- `prosperity-4-strategy-engineer`
- `prosperity-4-round2-alpha-finder`
- `prosperity-4-round2-log-analyst`
- `prosperity-4-round2-autopilot`

### 4. The repository now has seven local project agents
Those are:
- `competition_research`
- `alpha_miner`
- `execution_risk`
- `log_analyst`
- `strategy_engineer`
- `validator`
- `round2_autopilot`

### 5. Default live workflow is now Round 2 first
ChatGPT should assume **Round 2 is the default local workflow context** unless the user explicitly asks for:
- tutorial work,
- Round 1-specific work,
- historical comparison.

This means prompts should usually default to:
- Round 2 datasets,
- Round 2 traders,
- Round 2 alpha registry,
- Round 2 logs and validation artifacts.

### 6. Raw CSVs remain the source of truth
The repository policy is:
- raw round CSVs in dataset/resource folders are authoritative,
- analyzer outputs and research notes are derived artifacts,
- prompts must not encourage replacing the raw data with a lossy pseudo-source-of-truth layer.

### 7. The analyzer now belongs to the research layer
The analyzer lives under:
- `prosperity-research/03_eda/round1/`

Use its outputs as analysis artifacts, not as the canonical raw data source.
If a Round 2 analyzer or Round 2 EDA area exists, prefer that for Round 2 alpha work.

### 8. Important gap still preserved
If the repo-root `AGENTS.md` mentions conceptual roles that do not have matching local `.codex/agents/*.toml` files, ChatGPT should not assume they are runnable local agents.

---

## Official Context Versus Local Backtester Context

ChatGPT must explicitly distinguish:

### Official live-round context
Use the official context files when prompts are about the current competition round.

At the active workflow stage, Round 2 matters most.
Key official-like working assumptions that should be verified from repo files before code changes include:
- products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`,
- position limits are 80 each,
- `bid()` matters in Round 2 for market-access-fee bidding,
- the market-access fee is a blind auction for extra quotes,
- the manual Round 2 budget-allocation task is separate from algo-trader logic.

### Local backtester / repo context
Use the repository’s current files, datasets, analyzer outputs, and run artifacts for:
- what datasets exist locally,
- how the current backtester behaves,
- what the current Round 2 baselines and candidates are,
- what the current alpha registry already knows,
- what the recent runs say.

### Public-repo context
Older public Prosperity repos are inspiration for:
- strategy archetypes,
- architecture patterns,
- diagnostics patterns,
- fair-value designs,
- inventory and execution ideas.

They are **not** authority for:
- current Round 2 mechanics,
- current syntax requirements,
- current local repo defaults,
- current dataset layout,
- current alpha-registry state.

---

## Source Hierarchy ChatGPT Must Preserve

When writing prompts for Codex, preserve this order:

1. Official Prosperity files and syntax/interface material for current facts.
2. This repository's current files, datasets, analyzer outputs, alpha registry, backtester behavior, and run artifacts.
3. Older public Prosperity repos only for reusable ideas about strategy, architecture, and diagnostics.

Prompts must never encourage Codex to treat older public repos as authority for:
- current round products,
- current round rules,
- hidden mechanics,
- current syntax requirements,
- current position limits,
- current Round 2 market-access-fee details.

---

## How ChatGPT Should Integrate The Local Skills Into Prompts

### 1. Alpha-finding prompts
For dedicated Round 2 alpha-discovery tasks, ChatGPT should usually include a line like:

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-round2-alpha-finder` skill.
```

That prompt should usually ask Codex to:
- read the current Round 2 assumptions,
- read the Round 2 alpha registry first,
- classify ASH and Pepper by market type,
- rank candidate alphas,
- deduplicate aggressively,
- update `prosperity-research/04_signal_notes/round2_alpha_registry.md`,
- write a compact ranked output without editing trader code.

### 2. Strategy-builder prompts
For Round 2 implementation tasks, ChatGPT should usually include a line like:

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-strategy-engineer` skill.
```

That prompt should usually ask Codex to:
- read the current Round 2 assumptions,
- read the Round 2 alpha registry,
- choose one dominant alpha or execution/risk refinement,
- create or edit a Round 2 trader variant,
- keep `bid()` logic separate from order-generation logic,
- update the registry with built or newly noticed ideas,
- state the exact next validation step.

### 3. Log-diagnosis prompts
For official-log or local-run diagnosis tasks, ChatGPT should usually include a line like:

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-round2-log-analyst` skill.
```

That prompt should usually ask Codex to:
- inspect official and local Round 2 artifacts,
- identify the dominant failure mode first,
- generate a compact diagnosis packet,
- update the alpha registry only when evidence clearly changes alpha status,
- recommend the next build target.

### 4. Full-autopilot prompts
Only use this when the user explicitly wants one chat to do the full Round 2 loop.

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-round2-autopilot` skill.
```

That prompt should usually ask Codex to:
- refresh assumptions and the alpha registry,
- choose one high-value unbuilt or under-tested alpha,
- implement the smallest defensible trader change,
- inspect the result or state the exact next validation command,
- update the alpha registry,
- finish with a stage-by-stage summary.

### 5. Mechanical repo tasks
ChatGPT does **not** need to mention a strategy skill for purely mechanical tasks such as:
- moving files,
- updating docs,
- reorganizing research folders,
- cleaning zip artifacts,
- changing non-strategy repo metadata.

---

## How ChatGPT Should Integrate The Project Roles Into Prompts

Only do this when the user actually wants:
- multi-stage research,
- role-based analysis,
- a full research-to-implementation pipeline,
- explicit division of responsibility.

### Role order for a full role-driven Round 2 workflow
Use this order by default:
1. `competition_research`
2. `alpha_miner`
3. `execution_risk` and/or `log_analyst` depending on the task
4. `strategy_engineer`
5. `validator`

Use `round2_autopilot` instead of that multi-role pipeline only when the user explicitly wants one chat to own the entire loop.

### Role responsibilities
Use this mapping in prompts:

- `competition_research`
  Verifies official current Round 2 facts, separates official from local/inferred/borrowed assumptions, and writes to `prosperity-research/01_assumptions/current_assumptions.md`.

- `alpha_miner`
  Analyzes Round 2 datasets and research artifacts, ranks candidate edges, deduplicates ideas, and writes to:
  - `prosperity-research/04_signal_notes/latest_signal_ranking.md`
  - `prosperity-research/04_signal_notes/round2_alpha_registry.md`

- `execution_risk`
  Diagnoses fill realism, inventory path, drawdowns, and counterfactual quote quality, and writes to `prosperity-research/05_execution_risk/latest_execution_risk_report.md`.

- `log_analyst`
  Performs explicit log/artifact forensics, generates diagnosis packets, and updates the alpha registry only when logs clearly change alpha status.

- `strategy_engineer`
  Is the default implementation owner. Only this role should edit trader code under `prosperity_rust_backtester/traders/` by default.

- `validator`
  Compares a named candidate against a named baseline, runs or specifies Round 2 backtests, inspects artifacts, and ends with a SHIP or REJECT decision in `prosperity-research/06_validation/latest_validation_report.md`.

- `round2_autopilot`
  Owns the full loop only when explicitly requested. It must still keep the stages logically separated even though one chat is doing them all.

### Role guardrails ChatGPT should preserve
Prompts should preserve these boundaries:
- only `strategy_engineer` edits trader code by default,
- `alpha_miner` does not edit trader code,
- `execution_risk` and `log_analyst` do not edit trader code by default,
- non-code roles write into `prosperity-research/`,
- `validator` should not approve without a named baseline,
- `round2_autopilot` should still keep one dominant change per iteration,
- the alpha registry must be read before proposing or building Round 2 alphas.

---

## Prompting Defaults ChatGPT Should Encourage

Unless the user explicitly wants something else, prompt Codex to:
- work in `prosperity_rust_backtester/` for implementation tasks,
- follow both `AGENTS.md` files,
- use the Round 2 dataset context by default,
- read `prosperity-research/01_assumptions/current_assumptions.md` first if relevant,
- read `prosperity-research/04_signal_notes/round2_alpha_registry.md` before proposing or building alphas,
- create a new trader variant instead of overwriting a strong baseline,
- keep the change narrow and attributable,
- backtest locally,
- inspect more than headline PnL,
- state the expected effect on PnL, inventory, execution quality, or MAF-bid EV.

For a typical Round 2 strategy prompt, ChatGPT should specify:
- target trader file,
- target Round 2 dataset or day,
- comparison baseline,
- whether a new variant should be created,
- the validation command to run or the exact next run to execute,
- what outcome should improve,
- whether the alpha registry must be updated.

For a typical Round 2 alpha prompt, ChatGPT should specify:
- what evidence source to analyze,
- what products are in scope,
- whether to update the registry,
- whether to write `latest_signal_ranking.md`,
- that trader code must not be edited.

---

## Analyzer And Research-Artifacts Guidance

The repository now has a clearer research/implementation split.

ChatGPT should usually prefer analyzer and research artifacts over raw-data dumps when writing prompts for alpha discovery or diagnosis.

Useful inputs include, if present:
- `prosperity-research/03_eda/round1/ai_strategy_context/strategy_brief.md`
- `prosperity-research/03_eda/round1/ai_strategy_context/product_params.json`
- any Round 2 EDA folder under `prosperity-research/03_eda/round2/`
- `prosperity-research/04_signal_notes/latest_signal_ranking.md`
- `prosperity-research/05_execution_risk/latest_execution_risk_report.md`
- `prosperity-research/06_validation/latest_validation_report.md`

Prompt-writing rule:
- for alpha discovery and diagnosis, prefer compact research artifacts and selected visuals over giant raw CSV or log dumps,
- for implementation, use those research artifacts plus explicit trader and dataset context,
- only fall back to raw CSVs or raw logs when the task specifically requires raw-level verification.

---

## Validation And Command Surface ChatGPT Should Reference

The preferred local implementation and validation surface remains:
- `prosperity_rust_backtester/README.md`
- `prosperity_rust_backtester/Makefile`

Useful prompt language:

```text
Backtest locally using the current Makefile/backtester workflow and report the exact command used.
```

Because local command surfaces may evolve, ChatGPT should prefer prompt language like:
- “use the current Makefile workflow”,
- “report the exact command used”,
- “use the explicit Round 2 dataset context unless told otherwise”,

instead of hard-coding stale example commands unless the user specifically wants command suggestions.

When prompting for validation, ask Codex to inspect:
- total PnL,
- per-day PnL,
- product-level contribution,
- inventory behavior,
- time spent near position limits,
- obvious adverse passive fills,
- relevant run artifacts such as `metrics.json`, `combined.log`, `submission.log`, or other current persisted artifacts if they exist in this repo.

---

## Prompt Anti-Patterns ChatGPT Should Avoid

Do not write vague prompts like:
- “make the trader better”
- “find alpha”
- “use all the agents”
- “build every promising alpha”

Do not write prompts that:
- fail to name the target trader,
- fail to name the Round 2 dataset or run context,
- ignore the alpha registry,
- blur tutorial / Round 1 / Round 2 products,
- assume public old repos are authoritative,
- ask non-code roles to edit trader code,
- ask `validator` to approve without a baseline,
- tell Codex to overwrite the best current trader without reason,
- encourage broad rewrites before diagnosing the dominant bottleneck,
- let the alpha-finder and strategy-builder chats rediscover the same idea without registry coordination.

---

## Recommended Prompt Shapes

### 1. Dedicated Round 2 alpha-finding prompt
Use this when the goal is alpha discovery only.

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-round2-alpha-finder` skill.

Do not edit trader code.

Goal:
Discover and rank net-new Round 2 alpha ideas for <products / dataset / artifacts>.

Context:
- official assumptions file: prosperity-research/01_assumptions/current_assumptions.md
- shared alpha registry: prosperity-research/04_signal_notes/round2_alpha_registry.md
- relevant EDA or analyzer outputs: <paths>
- current issue or question: <brief statement>

Constraints:
- read the alpha registry first
- deduplicate aggressively
- separate high-confidence from speculative ideas
- write/update latest_signal_ranking.md and the shared alpha registry
- do not edit trader code

Done when:
- product classification is stated
- top alpha families are ranked
- duplicates are merged or rejected
- the next one or two build targets are named
```

### 2. Dedicated Round 2 strategy-builder prompt
Use this by default for implementation.

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-strategy-engineer` skill.

Work in `prosperity_rust_backtester/`.

Goal:
Build one dominant Round 2 alpha or execution/risk refinement into <trader file> while preserving submission compatibility.

Context:
- target trader: <path>
- baseline: <path>
- dataset: <round2 / specific day / specific run>
- official assumptions file: prosperity-research/01_assumptions/current_assumptions.md
- shared alpha registry: prosperity-research/04_signal_notes/round2_alpha_registry.md
- ranked signal file: prosperity-research/04_signal_notes/latest_signal_ranking.md
- diagnosis file if relevant: <path>

Constraints:
- read and update the shared alpha registry
- prefer one dominant change
- create a new Round 2 trader variant unless overwriting is explicitly requested
- keep `bid()` logic separate from order-generation logic
- do not touch `Trader1/`
- separate official facts from inferred assumptions

Done when:
- the code change is localized and attributable
- the alpha registry is updated
- the exact next validation step is stated
- the expected effect is explained
```

### 3. Dedicated Round 2 log-diagnosis prompt
Use this when the user provides logs or artifacts.

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-round2-log-analyst` skill.

Do not edit trader code by default.

Goal:
Analyze the named Round 2 logs and run artifacts, identify the dominant failure mode, and produce the next actionable diagnosis.

Context:
- target trader: <path if relevant>
- baseline: <path if relevant>
- run artifacts: <paths>
- shared alpha registry: prosperity-research/04_signal_notes/round2_alpha_registry.md

Constraints:
- identify the dominant failure mode first
- distinguish fair, threshold, passive-fill, inventory, state, and MAF-bid issues
- write or update the execution-risk report and diagnosis packet
- update the alpha registry only if evidence clearly confirms, falsifies, or merges an alpha
- do not build code unless explicitly asked

Done when:
- the dominant failure mode is named
- evidence is summarized compactly
- the next build target is recommended
- registry changes, if any, are explicit
```

### 4. One-chat Round 2 autopilot prompt
Use only when the user explicitly wants one chat to own the whole loop.

```text
Use the repo's AGENTS.md guidance and the `prosperity-4-round2-autopilot` skill.

Treat this as a full Round 2 loop in one chat.

Goal:
Refresh the alpha picture, choose one high-value target, implement the smallest defensible change, inspect the resulting evidence or state the exact next validation step, and update the shared alpha registry.

Context:
- assumptions file: prosperity-research/01_assumptions/current_assumptions.md
- alpha registry: prosperity-research/04_signal_notes/round2_alpha_registry.md
- ranked signal file: prosperity-research/04_signal_notes/latest_signal_ranking.md
- latest execution-risk report: prosperity-research/05_execution_risk/latest_execution_risk_report.md
- latest validation report: prosperity-research/06_validation/latest_validation_report.md

Constraints:
- keep the stages logically separate even though one chat is doing them all
- one dominant change only
- default to Round 2 datasets and traders
- never finish without updating the alpha registry

Done when:
- the chosen target is justified
- one implementation step is completed or clearly staged
- the registry is updated
- the next validation signal is named
```

### 5. Multi-stage role-driven Round 2 prompt
Use only when the user explicitly wants a role-based workflow.

```text
Use the repo's AGENTS.md guidance. Treat this as a role-driven Round 2 workflow.

Order of work:
1. `competition_research` verifies official current Round 2 facts and writes current_assumptions.md.
2. `alpha_miner` analyzes Round 2 datasets, EDA outputs, and run artifacts, then updates latest_signal_ranking.md and round2_alpha_registry.md.
3. `execution_risk` and/or `log_analyst` diagnoses fill realism, inventory path, and artifact evidence.
4. `strategy_engineer` implements the single best next change in `prosperity_rust_backtester/traders/`.
5. `validator` compares the candidate against the named baseline and ends with SHIP or REJECT.

Task:
<clear task>

Constraints:
- only `strategy_engineer` edits trader code
- non-code outputs go under `prosperity-research/`
- keep one dominant change per iteration
- use the alpha registry as shared coordination state
- default to Round 2 unless explicitly told otherwise
```

---

## What ChatGPT Should Usually Return To The User

When the user asks ChatGPT to generate a Codex prompt, ChatGPT should usually return:

1. one short note on what the prompt is optimized for,
2. one polished prompt in a code block,
3. optionally one stronger alternative for a role-based or autopilot workflow.

The prompt should usually be written in direct imperative language to Codex.

---

## Bottom Line

If ChatGPT remembers only a few rules, they should be these:

1. Tell Codex to follow the repo `AGENTS.md` files instead of pasting them.
2. Default to **Round 2** unless the user explicitly wants tutorial or Round 1 work.
3. Use the correct local skill for the correct chat:
   - `prosperity-4-round2-alpha-finder` for alpha discovery,
   - `prosperity-4-strategy-engineer` for implementation,
   - `prosperity-4-round2-log-analyst` for diagnosis,
   - `prosperity-4-round2-autopilot` only for one-chat full-loop work.
4. Treat `.codex/agents/*.toml` as project roles, not installable skills.
5. Preserve the official-vs-local-vs-public-repo source hierarchy.
6. Use the shared Round 2 alpha registry so alpha discovery and implementation do not duplicate each other.
7. Ask for one dominant change, a concrete validation step, and a named baseline whenever validation matters.
