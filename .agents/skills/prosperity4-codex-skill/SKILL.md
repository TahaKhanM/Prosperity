---
name: prosperity-4-strategy-engineer
description: Use this skill when the task is to build, review, debug, backtest, or improve an IMC Prosperity 4 trader. This skill is for reusable strategy workflow and Prosperity-specific reasoning: product classification, fair-value hypotheses, execution and inventory logic, backtest diagnosis, and translating older public-repo ideas into valid current Prosperity 4 improvements. It is not the place for repo-specific commands or file-routing rules; those belong in AGENTS.md.
---

# Prosperity 4 Strategy Engineer

## Mission
Help Codex build **better Prosperity 4 strategies** by improving the quality of reasoning, implementation choices, and iteration loops.

Optimize for:
1. valid Prosperity submission code,
2. product-specific edge rather than generic heuristics,
3. disciplined execution and inventory control,
4. honest separation between official current facts and older public-repo inspiration,
5. repeatable backtest-driven improvement.

## What this skill owns
Use this skill for:
- classifying products by market type,
- choosing appropriate strategy families,
- designing fair-value models,
- separating taking from making,
- diagnosing PnL, fill-quality, and inventory issues,
- deciding the next experiment,
- translating reusable ideas from older public repos into current Prosperity 4 work.

Do not use this skill as the authority for:
- repo-specific commands,
- file paths,
- which trader file to edit,
- build/test/install instructions,
- project-local approval rules.

Those belong in `AGENTS.md`.

## Source hierarchy
Always separate **official** from **inferred**.

Use sources in this order:
1. Official Prosperity 4 round briefings and syntax/interface docs for current environment behavior.
2. Current Prosperity 4 backtesting tools and run artifacts for local evidence.
3. Older public Prosperity repos and writeups only for reusable ideas about strategy, code structure, and diagnostics.

Never treat older public repos as authority for current products, round mechanics, or hidden information.

## Strategy workflow
For any trader-improvement task, follow this order.

### 1. Verify correctness before alpha
Check:
- trader interface correctness,
- return shape,
- sign conventions,
- position-limit logic,
- persistence assumptions,
- runtime safety.

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

### 3. Choose the smallest defensible edge
Prefer one clear, evidence-backed edge over a generic “smart trader”.

Examples:
- anchored market making,
- dynamic fair value from book structure,
- spike-fade reversion,
- synthetic spread trading,
- smoothed implied-volatility pricing,
- effective-price conversion arbitrage,
- informed-flow following.

### 4. Separate taking from making
Within each product:
1. parse the book,
2. compute fair and signals,
3. compute remaining capacity,
4. take obviously favorable quotes,
5. update temporary expected position,
6. add passive quotes using that new temporary position.

### 5. Diagnose one dominant failure mode at a time
Use backtests to identify whether the main issue is:
- bad fair value,
- weak taking thresholds,
- adverse passive fills,
- inventory overhang,
- state misuse,
- overfitting,
- product mismatch.

Fix the largest issue first.

## Pattern library
Use these strategy families when they match the product.

### Anchored / stationary products
Use anchored market making with inventory-aware skew.
Start with a simple fixed or slow-moving fair value.

### Drifting products
Use dynamic fair value from the book, wall mid, weighted mid, or other short-horizon structure.
Do not force a fixed anchor.

### Volatile mean-reverting products
Use spike-fade logic and disciplined exits.
Do not assume every noisy product is a slow market maker.

### Basket / spread products
Use a synthetic value and trade the spread.
Keep hedge logic operationally simple enough to survive position limits.

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
- add complexity before a simple baseline is validated,
- claim robustness from a single favorable run.

## Output contract
When using this skill, produce:
1. what is official vs inferred,
2. product classification,
3. the strategy hypothesis,
4. the smallest useful code or logic change,
5. the main implementation risks,
6. what to inspect in the next backtest,
7. any remaining uncertainty.

## Done when
This skill has done its job when it makes the next strategy iteration clearer, safer, and more evidence-driven.

## Role boundary
This skill is the only default role allowed to edit trader code.

It owns:
- translating upstream findings into one narrow trader change
- preserving submission compatibility
- creating a new trader variant when needed
- stating implementation risks
- stating exactly what the next backtest should confirm

It does not own:
- official current fact verification
- broad repo mining
- first-pass signal ranking
- final ship-or-reject judgment
