---
name: prosperity-4-strategy-engineer
description: Use this skill when the task is to build, review, debug, backtest, redesign, or improve an IMC Prosperity trader. This skill is for reusable strategy workflow and Prosperity-specific reasoning across tutorial and live rounds: round-aware interface checks, product classification, fair-value hypotheses, execution and inventory logic, backtest diagnosis, and translating older public-repo ideas into valid current Prosperity improvements. It is not the place for repo-specific commands or file-routing rules; those belong in AGENTS.md.
---

# Prosperity Strategy Engineer

## Mission
Help Codex build **better Prosperity traders** by improving the quality of reasoning, implementation choices, and iteration loops.

Optimize for:
1. official submission correctness for the current round,
2. product-specific edge rather than generic heuristics,
3. disciplined execution and inventory control,
4. honest separation between official current facts and older public-repo inspiration,
5. repeatable evidence-driven improvement,
6. choosing the **right scope of change**: focused patch, medium refactor, hybrid redesign, or clean-sheet rewrite.

## What this skill owns
Use this skill for:
- identifying the current round constraints that affect trader code,
- classifying products by market type,
- choosing appropriate strategy families,
- designing fair-value and execution logic,
- separating taking from making,
- diagnosing PnL, fill-quality, inventory, and state issues,
- deciding whether the next step should be a small fix or a larger redesign,
- translating reusable ideas from older public repos into current Prosperity work.

Do not use this skill as the authority for:
- repo-specific commands,
- file paths,
- which exact file to edit,
- build/test/install instructions,
- project-local approval rules.

Those belong in `AGENTS.md`.

## Source hierarchy
Always separate **official** from **inferred**.

Use sources in this order:
1. Official Prosperity round briefings and syntax/interface docs for current environment behavior.
2. Current backtesting tools, datasets, and run artifacts for local evidence.
3. Older public Prosperity repos and writeups only for reusable ideas about strategy, code structure, and diagnostics.

Never treat older public repos as authority for current products, round mechanics, hidden information, or submission interface details.

## Round-aware workflow
Before proposing strategy changes, verify what round you are actually solving.

Check:
- current tradable products,
- product limits,
- whether the round introduces non-trader side tasks such as auctions or manual components,
- whether the round changes trader interface requirements,
- whether methods such as `bid()` are required for the current round,
- whether conversions or observations matter for the current products.

Treat non-trader tasks as context, not as permission to contaminate the trader implementation with irrelevant logic.

## Strategy workflow
For any trader task, follow this order.

### 1. Verify correctness before alpha
Check:
- trader interface correctness,
- return shape,
- sign conventions,
- position-limit logic,
- persistence assumptions,
- runtime safety,
- round-specific method requirements.

### 2. Classify each product
Assign each product to the most plausible market type:
- anchored / stationary,
- drifting,
- volatile but mean-reverting,
- basket-linked / relative-value,
- derivative-like,
- conversion-linked,
- event-driven / informed-flow driven.

State the fair-value mechanism before proposing code.

### 3. Search the design space before choosing scope
Generate plausible candidate strategy families for the touched products.
For each candidate, ask:
- what market hypothesis it assumes,
- what evidence supports it,
- what evidence weakens it,
- whether the current implementation is weak because of the family or because of execution details,
- whether improvement likely requires a patch, refactor, hybrid, or rewrite.

Do not default to the smallest change by inertia.
Choose the **smallest change that actually attacks the dominant bottleneck**.
If the current strategy family is falsified by the data, allow a broader redesign.

### 4. Separate taking from making
Within each product:
1. parse the book,
2. compute fair and signals,
3. compute remaining capacity,
4. take clearly favorable quotes,
5. update temporary expected position,
6. add passive quotes using that new temporary position.

### 5. Diagnose one dominant failure mode at a time
Use backtests to identify whether the main issue is:
- bad fair value,
- weak taking thresholds,
- adverse passive fills,
- inventory overhang,
- state misuse,
- product mismatch,
- overfitting,
- false confidence from optimistic local fill assumptions.

Fix the largest issue first, but do not preserve an inferior architecture just to keep the diff small.

## Pattern library
Use these strategy families when they match the product.

### Anchored / stationary products
Use anchored market making with inventory-aware skew.
Start with a simple fixed or slow-moving fair value.
But still test whether quote placement, sizes, or inventory response can be improved materially.

### Drifting products
Use dynamic fair value from the book, wall mid, weighted mid, microprice, or other short-horizon structure.
Do not force a fixed anchor.

### Volatile mean-reverting products
Use spike-fade logic and disciplined exits.
Do not assume every noisy product is a passive market-maker.

### Basket / spread products
Use a synthetic value and trade the spread.
Keep hedge logic simple enough to survive position limits and latency-free matching behavior.

### Derivative-like products
Use theory as a base, but smooth noisy inputs such as implied volatility.
Prefer robust mispricing signals to fragile full-theory perfection.

### Conversion-linked products
Compare effective local and external prices after fees and constraints.
Treat conversion as a specialized inventory transformation problem.

### Event-driven / informed-flow products
Use counterparty or event logic only when there is clear evidence that it matters.

## Anti-patterns
Do not:
- recommend generic indicators with no product-level hypothesis,
- blur official current facts with older repo ideas,
- mix aggressive and passive logic into one opaque block,
- ignore worst-case position usage,
- add complexity before falsifying simpler alternatives,
- claim robustness from one favorable run,
- reject a full redesign only because the current baseline is familiar.

## Output contract
When using this skill, produce:
1. what is official vs inferred,
2. round-aware interface and constraint checks,
3. product classification,
4. candidate strategy families considered,
5. the chosen strategy hypothesis,
6. why the chosen implementation scope is appropriate,
7. the main implementation risks,
8. what to inspect in the next backtest,
9. any remaining uncertainty.

## Done when
This skill has done its job when it makes the next trader iteration clearer, safer, and more evidence-driven, and when the chosen scope of implementation is justified by the data rather than by habit.

## Role boundary
This skill is the default role allowed to translate findings into trader-code decisions.

It owns:
- turning upstream findings into the best next implementation step,
- preserving submission compatibility,
- creating a new trader variant when needed,
- allowing a hybrid redesign or clean-sheet trader when warranted,
- stating implementation risks,
- stating exactly what the next backtest should confirm.

It does not own:
- official current fact verification beyond identifying what must be checked,
- broad repo mining,
- first-pass signal ranking,
- final ship-or-reject judgment.
