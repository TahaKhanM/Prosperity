# IMC Prosperity 4 Strategy Research Foundation

## Executive summary

entity["company","IMC Trading","quant trading firm"]’s Prosperity 4 is a five‑round algorithmic + manual trading challenge running 14–30 April 2026, preceded by a “tutorial round” (16 March–13 April). citeturn44view0 The official public landing page is high-level and the public entity["company","Notion","productivity platform"] wiki link appears to be gated or moved (a direct fetch returned 404), so correctness on mechanics should be anchored in the official interface/syntax document you supplied (uploaded “official_prosperity_context.md”) plus any round-specific PDFs/announcements as they appear. fileciteturn0file0 citeturn44view0

The strongest “still-relevant” public foundation for Prosperity 4 is a combination of:
- **Prosperity 4-era tooling**: a modern, tutorial‑round focused Monte Carlo backtester + visualiser (entity["company","GitHub","code hosting platform"] repo `chrispyroberts/imc-prosperity-4`) and a deterministic replay backtester (`nabayansaha/imc-prosperity-4-backtester`) that documents order matching and limit enforcement assumptions. citeturn47view0turn48view0  
- **Top Prosperity 3 codebases** (especially ranks 2, 7, 9, 10) that show robust architecture patterns: product‑specific modules, fair value estimation under noisy books, inventory-aware quoting, opportunistic taking, and round‑specific additions (baskets, options, conversions, known-signal following). citeturn4view0turn13view0turn19view0turn35view2  
- **Prosperity 2 “Linear Utility” writeup + code** (rank 2) which is unusually explicit about backtesting discipline, market-maker mid “true fair” behaviour, and a clean decomposition of take/clear/make workflows. citeturn41view0turn43view1turn43view3

Across those codebases, the most reusable Prosperity‑4‑likely ideas (especially for tutorial products analogous to “fixed fair” + “random walk fair”) are:
- anchored fair-value market making with **inventory-skewed spread placement**,
- opportunistic taking around a computed fair (often a filtered “market-maker mid”),
- “clear-to-zero” position flattening at neutral/fair prices to preserve future capacity,
- lightweight regime filters (volatility spikes, trend/momentum) to turn off one side or reduce size,
- engineering habits: **backtesting + visual debugging + log-size hygiene** for fast iteration under tight runtime and output constraints. citeturn47view0turn48view0turn35view2turn21view2turn43view1

Later-round mechanics (baskets/spreads, options, conversions, known “insider” IDs) are historically common in Prosperity 2/3, but should be treated as **probable motifs rather than guaranteed** for Prosperity 4 until official round releases confirm exact products and rules. citeturn44view0turn46search2turn41view0turn16view0

## Source map

This catalogue is organised by “authority first”: official materials, then high-signal repos (ranked teams + tooling), then community aggregators/discussions, then background microstructure resources. “Current/stale” is judged relative to Prosperity 4 (April 2026) and whether the source targets Prosperity 4 directly.

### Official / correctness anchors

**Prosperity 4 main site (schedule, high-level rules, entry points)**  
URL: `https://prosperity.imc.com/` citeturn44view0turn46search5  
Type: official web page  
Code/explanation: explanation (platform overview)  
Usefulness: high for dates, eligibility, and official pointers; low for trading mechanics  
Current/stale: current (2026 context and schedule are explicit) citeturn44view0  
Unique insight: public schedule + structure (tutorial round; 5 rounds; dates) citeturn44view0  
Reusable vs round-specific: reusable context only

**Uploaded “official_prosperity_context.md” (interface/syntax document)**  
URL: (local upload) fileciteturn0file0  
Type: official syntax/interface material (as provided by you)  
Code/explanation: both (interface + constraints)  
Usefulness: **highest**—treat as the ground truth for `Trader.run`, state objects, and constraints  
Current/stale: presumed current for Prosperity 4 unless contradicted by new official releases  
Unique insight: authoritative mechanics (state fields, logging/traderData limits, timing model)  
Reusable vs round-specific: core reusable

### Hub / curated index

**Ctrl‑Alt‑DefeatTheMarket (public hub + link index + meta-framework)**  
URL: `https://github.com/MarkBrezina/Ctrl-Alt-DefeatTheMarket` citeturn46search2  
Type: hub repository / curated reading list  
Code/explanation: explanation + links (some starter code links referenced) citeturn46search2  
Usefulness: high for source discovery (lists many ranked repos and some microstructure resources) citeturn46search2  
Current/stale: written for Prosperity 4 preparation; “Round 1 not started yet” note indicates pre‑Round‑1 timing but still very relevant for discovery citeturn46search2  
Unique insight: frames Prosperity as 5 engines (alpha/risk/inventory/execution/portfolio) and enumerates many repos worth mining citeturn46search2  
Reusable vs round-specific: mostly reusable planning + links; any included “quick profit” sample is tutorial/round‑0 specific

### Prosperity 4 tooling (highest immediate leverage)

**P4 Monte Carlo backtester + Rust simulator + dashboard visualiser (chrispyroberts)**  
URL: `https://github.com/chrispyroberts/imc-prosperity-4` citeturn47view0  
Type: tooling repository  
Code/explanation: both; includes CLI + visualiser + tutorial product models citeturn47view0  
Likely usefulness: **very high** for robustness testing (distributional PnL, stability) and fast iteration  
Current/stale: current (explicitly Prosperity 4 tutorial-round focus) citeturn47view0  
Unique insight:
- provides a **generative** Monte Carlo model for tutorial products (explicit fair models: fixed fair for EMERALDS; latent random-walk fair for TOMATOES) citeturn47view0  
- offers a “drop-in” interface compatibility (no need to rewrite `Trader.run`) citeturn47view0  
Reusable vs round-specific: reusable tooling; tutorial modelling assumptions are round‑0 specific

**P4 deterministic replay backtester (nabayansaha; fork lineage from jmerle)**  
URL: `https://github.com/nabayansaha/imc-prosperity-4-backtester` citeturn48view0  
Type: tooling repository (backtester + CLI package)  
Code/explanation: both; includes explicit order matching description citeturn48view0  
Likely usefulness: **very high** for local regression tests, fast iteration, and reproducibility  
Current/stale: current; explicitly Prosperity 4; data “added as available” citeturn48view0  
Unique insight:
- documents a detailed matching model: fill against order depths first, then optionally match against market trades; and notes a specific seeming “official-like” behaviour where a market trade at 10 can fill your sell quote at 9 at 9 (your price), not at the trade price citeturn48view0  
- documents position limit enforcement and tutorial limits: 80 for EMERALDS and TOMATOES (with fallback defaults) citeturn48view0  
Reusable vs round-specific: reusable; but treat matching rules as “best-effort reverse engineering” unless confirmed by official docs

### Best-in-class team repos (Prosperity 3 and 2)

**entity["organization","Frankfurt Hedgehogs","prosperity 3 team"] (Prosperity 3 rank 2) – deep writeup + full final code**  
URL: `https://github.com/TimoDiehm/imc-prosperity-3` citeturn15search10turn4view0  
Type: team repo (code + writeup)  
Code/explanation: both; large single-file final algorithm plus narrative; multiple product modules citeturn4view0turn8view0  
Likely usefulness: **exceptional** as a “reference architecture” for multi-product competition bots  
Current/stale: Prosperity 3 (2025) mechanics may differ; strategy patterns remain highly reusable citeturn15search10turn46search2  
Unique insight: a full multi-asset system with:
- explicit product trader classes (static/dynamic/ETF/option/commodity) citeturn5view0turn8view0  
- “wall” based fair estimation for simple products (bid/ask walls, wall-mid) citeturn5view0  
- options trading with implied vol surface fitting + IV scalping + mean reversion blend citeturn8view0turn9view0  
Reusable vs round-specific: architecture, wall-mid/predictable-maker logic reusable; the exact products (ETF constituents, strikes) are round-specific citeturn8view0turn9view0

**Prosperity 3 rank 7 – repo with iterative versions + heavy diagnostics (chrispyroberts)**  
URL: `https://github.com/chrispyroberts/imc-prosperity-3` citeturn10view0turn12view0  
Type: team repo (code + some writeup)  
Code/explanation: both in practice (README + many code versions per round) citeturn11view0turn14view3  
Likely usefulness: very high for seeing evolution and how teams debugged and tuned  
Current/stale: Prosperity 3 (2025); patterns remain reusable  
Unique insight:
- explicit fair = mid of outer book levels, plus “search” functions to take favourable orders and “market made” quotes shifted around fair citeturn13view0turn14view1  
- regime control on a volatile product: volatility thresholds, trend-based turning off a side, and “flash crash” style heuristics citeturn14view3  
Reusable vs round-specific: general; the specific thresholds/products are round-specific citeturn14view4

**entity["organization","Alpha Animals","prosperity 3 team"] (Prosperity 3 rank 9) – writeup + consolidated trader**  
URL: `https://github.com/CarterT27/imc-prosperity-3` citeturn16view0turn17view0  
Type: team repo (writeup + final trader)  
Code/explanation: both; `trader.py` is large and includes multiple product strategies citeturn16view0turn22view1  
Likely usefulness: very high; especially good for basket + options patterns  
Current/stale: Prosperity 3 (2025) mechanics; patterns reusable  
Unique insight:
- systematic fair value helper (best bid/ask mid) + “clear position” logic that actively offloads inventory at fair when liquidity exists citeturn18view1turn22view1  
- explicit basket synthetic value model and divergence trading; and separate “execute basket arbitrage” that trades basket vs component depths under constraints citeturn19view0turn22view2  
- options support: Black‑Scholes call, delta, vega, implied vol (Newton iterations), strike-spread arbitrage checks, and basic stop-loss/profit-target hooks citeturn21view1turn29view0turn28view1  
Reusable vs round-specific: tooling patterns reusable; coefficients/strikes and product list round-specific citeturn20view0turn28view1

**entity["organization","Team Theta Drip","prosperity 3 team"] (Prosperity 3 rank 10) – detailed narrative + per-round submissions**  
URL: `https://github.com/YBansal95/imc-prosperity-3` citeturn31view0turn33view0  
Type: team repo (writeup + per-round code)  
Code/explanation: both; explicit round-by-round strategy in README plus the actual code files `round1.py` … `round5.py` citeturn31view0turn32view0turn35view2  
Likely usefulness: high—excellent for “how a top team iterated”  
Current/stale: Prosperity 3 (2025); many patterns still relevant  
Unique insight:
- fair value estimation via **filtered market-maker quotes** (min ask among large asks; max bid among large bids) for KELP, plus VWAP tracking; then taking + making around that fair citeturn35view2turn35view3  
- explicit state persistence via `traderData` and log truncation helpers (careful about JSON-escaped size) citeturn34view0turn38view3  
Reusable vs round-specific: fair filtering + execution scaffolding reusable; later-round strategies depend on products and signals citeturn31view0turn39view2

**entity["organization","Linear Utility","prosperity 2 team"] (Prosperity 2 rank 2) – writeup + code + internal tools**  
URL: `https://github.com/ericcccsliu/imc-prosperity-2` citeturn41view0  
Type: team repo (writeup-heavy + code + tools)  
Code/explanation: both; unusually detailed about backtester and dashboard design citeturn41view0  
Likely usefulness: **exceptional** for foundational market making, backtesting workflow, and “true fair” discussions  
Current/stale: Prosperity 2 (2024) products differ, but core approach remains among the best references  
Unique insight:
- clean decomposition in code into **take_orders → clear_orders → make_orders**, with configurable parameters per product and a fair-value model for a drifting product using a market-maker mid plus a mean-reversion correction citeturn43view1turn43view3  
- writeup highlights that marking-to-market may align with a large market maker’s mid, motivating robust fair estimation from “trusted” volume levels citeturn41view0turn43view3  
Reusable vs round-specific: extremely reusable design; the exact params/products are round-specific citeturn43view0turn43view1

### Community discovery sources (useful, but not authoritative)

**entity["company","Reddit","social platform"] threads aggregating repo links and advice**  
URL: `https://www.reddit.com/r/quantfinance/comments/1s2gyoe/imc_prosperity_4/` citeturn15search17turn15search2  
Type: discussion + link aggregation  
Code/explanation: explanation (varies)  
Usefulness: medium for discovery; low for correctness  
Current/stale: current (posted ~2 weeks prior to your request) citeturn15search17  
Unique insight: crowdsourced shortlist of Prosperity 3 repos + pointers to Optiver competitions citeturn15search2  
Reusable vs round-specific: discovery only

### Microstructure & trading theory resources (background, directly relevant)

**Avellaneda–Stoikov market making model (limit order book)**  
URL: `https://people.orie.cornell.edu/sfs33/LimitOrderBook.pdf` citeturn49search0  
Type: research paper (PDF)  
Code/explanation: explanation (math + model)  
Usefulness: high—canonical foundation for inventory‑aware quoting and optimal spread under risk  
Current/stale: timeless; model assumptions should be adapted to Prosperity mechanics  
Unique insight: formalises the trade-off between spread capture and inventory/price risk in a LOB setting citeturn49search0  
Reusable vs round-specific: reusable theory

**Micro-price as an order-book-based “fair” estimator**  
URL: `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2970694` citeturn49search11  
Type: research paper (SSRN)  
Code/explanation: explanation  
Usefulness: high for Prosperity because many products have a “noisy mid” and meaningful imbalance signals  
Unique insight: micro-price adjusts mid by spread + imbalance and can be treated as conditional fair citeturn49search11  
Reusable vs round-specific: reusable

**Recent microprice modelling (higher-order imbalance dynamics)**  
URL: `https://arxiv.org/html/2411.13594v1` citeturn49search3  
Type: research paper (arXiv)  
Code/explanation: explanation  
Usefulness: medium-high; more complex than most Prosperity bots will need, but helpful if depth/imbalance features matter  
Unique insight: adds error-correction dynamics over microprice using higher-rank imbalances citeturn49search3  
Reusable vs round-specific: reusable

**Algorithmic & HFT textbook reference (covers adverse selection, execution, market making)**  
URL: `https://assets.cambridge.org/97811070/91146/frontmatter/9781107091146_frontmatter.pdf` citeturn49search5  
Type: book (publisher PDF front matter)  
Code/explanation: explanation  
Usefulness: high as a structured reference; less directly “drop-in” than public Prosperity repos  
Unique insight: connects optimal execution + market making concepts with microstructure considerations like adverse selection citeturn49search5  
Reusable vs round-specific: reusable

## Best public repos to study deeply

This list prioritises (a) demonstrated performance, (b) presence of real final code, and (c) transferable engineering patterns. For each, I summarise fair value, execution, inventory/risk, architecture, and what appears robust vs hacky/round-specific.

### Frankfurt Hedgehogs (Prosperity 3 rank 2) – TimoDiehm/imc-prosperity-3

Fair value logic: for “simple” products they use a “walls” abstraction (bid wall = best bid level, ask wall = best ask level, wall mid = average) as a base fair; they also implement dynamic variants that react to informed flow. citeturn5view0turn6view0

Execution logic: structured around `ProductTrader` primitives like `bid()`/`ask()` with max-allowed sizing computed from position limits and the current position; this makes execution consistent across products. citeturn6view0

Inventory/risk logic: explicit per-product position limits (via `POS_LIMITS`) and consistent “max allowed volume” calculations that clamp orders to what keeps worst-case fills within limits. citeturn6view0

Architecture & backtesting workflow: one consolidated file (`FrankfurtHedgehogs_polished.py`) but internally modularised into multiple trader classes (static, dynamic, ETF, option, and commodity). This is a practical “submission-friendly” architecture: modular logic without multi-file imports. citeturn5view0turn8view0

Robust elements likely reusable in Prosperity 4:
- the **product-trader abstraction** (shared sizing helpers, shared orderbook parsing, shared risk clamps) is a strong template for P4 multi-product rounds. citeturn6view0turn8view0  
- options methods show implementable implied‑vol fitting and IV‑signal trading patterns that can be simplified if P4 introduces derivatives again. citeturn8view0turn9view0  
- commodity + conversion logic illustrates careful accounting of transport/tariff terms when deciding to convert and/or arb. citeturn9view0  

Round-specific or “hacky” components:
- ETF composition, specific strikes, and specific thresholds/EMAs are tightly dependent on Prosperity 3 product design and should be treated as motifs, not plug‑and‑play. citeturn8view0turn9view0

### chrispyroberts/imc-prosperity-3 (Prosperity 3 rank 7) – Round 1 final trader

Fair value logic: for KELP and SQUID_INK it computes a fair price as an average of book-derived prices and then makes a spread around it; for fixed-fair products (RAINFOREST_RESIN) it uses hard-coded anchors around 10,000. citeturn13view0turn14view1

Execution logic:  
- “search_buys/search_sells” functions sweep depth levels to take mispriced liquidity relative to fair/acceptable price. citeturn13view1turn13view0  
- “market made” quotes are adjusted if another market maker’s top-of-book is better (joins/improves). citeturn13view0turn14view1  

Inventory/risk logic: explicit per-product caps (±50 in round 1), plus tracking of current tick’s submitted buy/sell amounts to avoid breaching limits even if everything filled. citeturn13view4turn14view4

Architecture & workflow: the repo contains many trader versions and notebooks per round, revealing a real iteration pipeline (optimisation scripts, manual checks, backtests directory). citeturn11view0turn11view0

Robust elements likely reusable:
- volatility and trend regime filters that disable one side or de-risk during unstable periods are generic and appear repeatedly in top repos. citeturn14view3  
- “other market maker present” logic (join/step ahead) is a realistic execution improvement for competitive books. citeturn13view0turn14view1  

Round-specific elements:
- specific window lengths and “BANANA ZONE” heuristics are clearly tuned to Squid Ink’s behaviour; treat them as a pattern (volatility gating), not the actual parameters. citeturn14view2turn14view3

### Alpha Animals (Prosperity 3 rank 9) – CarterT27/imc-prosperity-3

Fair value logic: baseline fair = (best bid + best ask)/2, with additional filters to compute a “market-maker mid” for KELP (filters large quotes) and per-product widths/thresholds. citeturn18view1turn18view2

Execution logic:
- includes both divergence trading (basket vs synthetic) and explicit multi-leg basket/component arbitrage using available depth. citeturn19view0turn22view2  
- options trading includes systematic IV inference and quoting around theoretical option prices. citeturn28view1turn21view1  

Inventory/risk logic:
- `clear_position_order` is a core primitive: if you’re net long/short after taking, it attempts to unload at fair when liquidity is present, to free capacity. citeturn18view1turn22view1  
- logging/truncation is engineered to stay within strict output constraints (reduces payload, omits trade lists, and allocates log budget). citeturn21view2turn21view3  

Architecture & workflow:
- a single `trader.py` with extensive helpers; config dictionaries for limits, widths, thresholds, and “active products” toggles for enabling/disabling strategies. citeturn19view0turn20view0  

Robust reusable elements:
- “clear-to-zero” capacity management is broadly useful in any bounded-position environment. citeturn18view1  
- option helper implementations (BS + IV via Newton) are a reusable template. citeturn21view1turn29view0  
- basket execution shows both “trade only basket” divergence and “trade legs” arb patterns; the latter is valuable if Prosperity 4 introduces convertible bundles again. citeturn22view2turn19view0  

Round-specific elements:
- linear coefficients, thresholds, strike sets, and stop-loss constants are tuned to Prosperity 3; reuse the structure, not the numbers. citeturn19view0turn28view1

### Team Theta Drip (Prosperity 3 rank 10) – YBansal95/imc-prosperity-3

Fair value logic: in round 1 code, KELP fair is computed from “filtered” book levels based on volume thresholds (market-maker quotes), and VWAP is tracked; SQUID_INK fair is similarly computed with smoothing across recent mids. citeturn35view2turn35view3

Execution logic: takes mispriced best bid/ask when they cross fair ± take_width, then places bids/asks at “best below fair + 1” / “best above fair − 1” to market make around fair. citeturn35view2

Inventory/risk logic: per-product limits and explicit buy/sell volume tracking; plus `clear_position_order` to flatten after taking. citeturn34view1turn35view2

Architecture & workflow: per-round submission files (`round1.py` … `round5.py`) makes it easy to map how strategies evolved; the README documents modelling steps (feature engineering, logistic regression idea, etc.) that can inspire P4 experimentation. citeturn31view0turn32view0

Robust reusable elements:
- market-maker mid filtering is extremely common in top teams; this repo is a clean, compact implementation. citeturn35view2  
- careful log/traderData truncation helpers show awareness of platform constraints. citeturn34view0turn38view3  

Round-specific elements:
- later-round modelling and product-specific details depend on Prosperity 3 design; use as inspiration. citeturn31view0turn39view2

### Linear Utility (Prosperity 2 rank 2) – ericcccsliu/imc-prosperity-2

Fair value logic:  
- fixed fair for stable products (10,000 anchor). citeturn41view0turn43view1  
- “drifty” product fair: compute a market-maker mid from large quotes; apply a small mean reversion correction using a beta on last return. citeturn43view3turn43view0  

Execution logic: a clean pipeline:
- `take_orders` for favourable liquidity, optionally with adverse selection filters,
- `clear_orders` to reduce exposure at ~0 EV levels,
- `make_orders` to provide quotes with configurable edges and join/disregard logic. citeturn43view1turn43view0

Inventory/risk logic: strict per product limits and a “soft position limit” concept to reduce aggression as inventory grows. citeturn43view0turn43view1

Architecture & backtesting workflow: the README describes an in-house backtester that reconstructs the full state, matches orders, simulates market making by attributing bot‑bot trades when your quotes are better, and emits logs matching platform format; plus a dashboard for visual inspection and parameter grid search. citeturn41view0

Robust reusable elements:
- decomposition into take/clear/make is the best reusable execution template for Prosperity. citeturn43view1  
- “clear orders” to preserve capacity is repeatedly rediscovered by top teams; this repo makes it explicit (and quantifies improvement in writeup). citeturn41view0turn43view1  
- engineering discipline (tools + grid search) is reusable regardless of products. citeturn41view0  

Round-specific elements:
- products and specific found “arbs” (e.g., the orchids conversion arb described in writeup) are competition‑specific; keep as pattern examples. citeturn41view0

## Cross-repo pattern synthesis

Across the strongest repos above (and corroborated by the Prosperity‑4‑era hub list), several patterns recur so consistently that they should be treated as “default baselines” for Prosperity 4 development. citeturn46search2turn35view2turn43view1turn6view0turn19view0

Anchored fair value market making is the backbone. For “fixed-fair” products, teams hardcode an anchor (10,000 equivalents) and focus on spread capture plus opportunistic taking; for “drifting” products they estimate fair from the book (often the large quote levels) and update it slowly. citeturn14view1turn35view2turn43view3turn47view0 The P4 tutorial modelling in the Monte Carlo repo explicitly mirrors this split: EMERALDS has fixed fair 10,000, TOMATOES a driftless latent process. citeturn47view0turn48view0

Dynamic fair value models are usually “microstructure-light”: rather than heavy prediction, top teams use robust book features (filtered market-maker mid, VWAP, short rolling means) and small corrections (mean reversion beta, EMA deviation). citeturn35view2turn43view3turn22view1turn6view0 This is consistent with microstructure theory that the mid alone can be noisy and that book imbalance can inform a conditional fair (micro-price). citeturn49search11turn49search7

Inventory-skewed quoting and “clear-to-zero” are universal once position limits bite. Multiple top repos implement an explicit “clear” step: if you’re near limits or simply net long/short after taking, you try to trade at (or very near) fair to free capacity for future positive-EV fills. citeturn34view1turn18view1turn39view1turn41view0 This aligns with the Avellaneda–Stoikov view that inventory risk is central to optimal quoting. citeturn49search0

Active taking is used opportunistically but selectively. Most teams implement “search” or “take” functions that traverse top levels and consume liquidity when price is favourable vs fair by some width. citeturn13view1turn35view2turn43view1turn6view0 In P4 backtester tooling, careful matching and limit enforcement strongly suggests that wrong‑sized aggressive orders can be penalised by cancellations or clamping, so “take” needs to be limit-aware and volume-aware. citeturn48view0

Regime filters are common for volatile products. Teams either (a) trade mean reversion on spikes, (b) trade momentum/trend filtered by volatility, or (c) turn off one side when directional risk is high. citeturn14view3turn22view1turn13view0turn16view0 The lesson for Prosperity 4 is not the specific window sizes, but the principle: some products are not profitable to naïvely market-make; you need “risk-off switches.” citeturn14view3turn16view0

Basket/spread/relative value logic appears whenever composites exist. The common approach is: compute a synthetic basket value as a linear combination of component mids, then trade divergence either (i) only in the composite (simpler execution) or (ii) as a full multi-leg arb (more complexity, potentially more edge). citeturn19view0turn22view2turn31view0turn38view4

Conversions and cross-venue mechanics are a major “gotcha.” Prosperity 2 and 3 included products where conversion-like operations or external observation costs mattered, and teams explicitly mention losses due to misunderstanding conversion costs or backtester limitations. citeturn16view0turn41view0turn9view0turn48view0 For Prosperity 4, the P4 backtester explicitly states conversions are not yet supported (for the tutorial data), reinforcing that conversion mechanics are round-dependent and tooling may lag. citeturn48view0turn47view0

Diagnostics and backtesting habits differentiate top teams more than any single “alpha trick.” Prosperity 2 rank‑2 built an in-house backtester + dashboard and explicitly grid-searched parameters; Prosperity 3 rank‑9 and rank‑10 built careful log truncation and state compression; Prosperity 4 tooling is now evolving toward Monte Carlo distributional testing. citeturn41view0turn21view2turn34view0turn47view0 In other words: the consistent advantage is iteration speed and correctness, not a secret indicator.

## Key algorithmic trading resources worth keeping

These are not Prosperity-specific, but they map tightly onto Prosperity mechanics (limit order book market making with inventory constraints, adverse selection, and execution).

The canonical formal model for inventory-aware market making is by entity["people","Marco Avellaneda","mathematician"] and entity["people","Sasha Stoikov","quant researcher"], modelling a dealer who posts bid/ask quotes under inventory risk and stochastic mid-price dynamics. citeturn49search0 This is directly relevant to Prosperity because most profitable tutorial/early-round strategies are variants of “quote around fair, skew with inventory.”

Micro-price research is especially relevant to Prosperity’s “noisy mid” problem. Stoikov’s micro-price formulation treats fair as a conditional expectation that adjusts mid by spread and top-of-book imbalance. citeturn49search11turn49search7 If Prosperity 4 markets again exhibit stable “large” market maker quotes plus many small noisy orders (as described in high-ranking Prosperity 2/3 writeups), micro-price-inspired fair estimation is a principled extension of the “filtered market-maker mid” heuristic. citeturn43view3turn35view2turn49search11 Recent work extends this further by incorporating higher-order imbalance dynamics (useful if deeper book levels matter in P4). citeturn49search3

For a structured reference that ties together execution, market making, and adverse selection, the textbook by entity["people","Álvaro Cartea","finance academic"], entity["people","Sebastian Jaimungal","mathematician"], and entity["people","José Penalva","economist"] is a useful “concept map” (even if you won’t implement the full models in Prosperity). citeturn49search5 The microstructure foundation text by entity["people","Maureen O'Hara","economist"] is helpful for understanding why certain order-book signals and adverse selection effects exist, though it is more theoretical than most Prosperity teams need. citeturn49search2turn49search22

Finally, for Prosperity‑specific iteration speed, the most “practically important” resource category is tooling and evaluation methodology: the P4 Monte Carlo backtester is a notable escalation in testing sophistication because it pushes teams toward measuring **edge stability** instead of overfitting to a small tutorial dataset. citeturn47view0turn46search12

## What should go into a Codex and Claude knowledge base

The knowledge base should be structured as “authoritative mechanics” + “reusable primitives” + “strategy templates” + “testing harnesses” + “anti-patterns”. The goal is to make coding agents effective without letting them hallucinate mechanics.

Authoritative mechanics layer:
- The complete Prosperity interface and datamodel as defined in your supplied official context doc (objects, required return values, constraints on runtime/output/traderData). fileciteturn0file0  
- A thin “mechanics delta log” that records any Prosperity 4 round release changes and links them to official sources (because Prosperity 2/3 repos are not authority for Prosperity 4). citeturn44view0  

Reusable coding primitives (pull from top repos and adapt):
- Order book utilities: best bid/ask, filtered market-maker levels, wall-mid, VWAP, imbalance, and micro-price-inspired fair. citeturn35view2turn5view0turn49search11  
- Execution helpers: `take_if_edge(fair, width)`, `make_quotes(fair, edge, inventory_skew)`, `join_or_improve_existing_mm`, and “depth sweep” order taking. citeturn13view1turn14view1turn6view0turn43view1  
- Risk & inventory helpers: strict max size under position limits, soft limits, and clear-to-zero functions. citeturn48view0turn18view1turn39view1turn43view0  
- State persistence and log hygiene patterns: safe compact JSON, truncation that accounts for JSON escaping, and minimal debug payloads. citeturn21view2turn34view0turn38view3  

Strategy templates (parameterised skeletons, not hard-coded numbers):
- Fixed-fair market making template (tutorial EMERALDS analogue) with take/clear/make stages and inventory skew. citeturn47view0turn43view1  
- Random-walk fair template (tutorial TOMATOES analogue) using filtered market-maker mid + light smoothing; includes “turn off” regimes when volatility spikes. citeturn47view0turn35view2turn14view3  
- Basket divergence + optional legging template (only activated if P4 introduces composite products). citeturn19view0turn22view2turn38view4  
- Options template: Black‑Scholes + implied vol + basic vol signal (only activated if P4 introduces options-like instruments). citeturn21view1turn8view0turn9view0  
- Conversion arb template: a decision function that computes all-in conversion costs and only converts if the net edge exceeds a safety margin (only activated once conversions exist and are confirmed). citeturn9view0turn48view0  

Testing harnesses (Prosperity 4-specific):
- Deterministic replay backtests using `prosperity4btest` (fast unit/regression tests) with explicit assumptions and “official mismatch” warnings. citeturn48view0  
- Monte Carlo distributional backtests for tutorial products using `prosperity4mcbt`, focusing on stability metrics (e.g., fraction profitable, drawdown tails) rather than a single sample path. citeturn47view0turn46search12  

A curated “patterns library”:
- A short set of “canonical patterns” with examples cited to the exact public implementation points (e.g., “filtered market-maker mid” from Theta Drip round1; “take/clear/make” from Linear Utility; “product-trader abstraction” from Frankfurt Hedgehogs). citeturn35view2turn43view1turn6view0  

## What should be excluded as low-value or stale

Any material that is (a) not mechanically reliable for Prosperity 4, (b) too generic to inform implementation decisions, or (c) lacks primary artefacts (no code and no concrete notes) should be excluded or quarantined.

Low-value as authority (keep only as inspiration, clearly labelled):
- Random Prosperity 1/2/3 repos with no final submission code or only partial notebooks. The hub list contains many placements; without inspecting code quality, treat these as discovery leads, not foundation. citeturn46search2  
- Community posts and threads (especially entity["company","Reddit","social platform"] summaries) are useful for finding links but are not reliable for mechanics or optimisation claims. citeturn15search17turn15search4  

Potentially stale mechanics (quarantine until confirmed by official docs each round):
- Any assumptions about conversions, market-trade matching, or position-limit enforcement drawn from backtesters. They are extremely helpful, but must be treated as “best-effort replication,” not guaranteed official behaviour. citeturn48view0turn47view0  
- Any product-specific coefficients/thresholds from Prosperity 2/3 (basket regressions, strike lists, IV thresholds, ETF composition, insider IDs). These are round designs, not general truths. citeturn19view0turn8view0turn31view0turn9view0  

Generic background that is not immediately actionable for Prosperity-style trading bots:
- Broad “how markets work” content that doesn’t connect to limit order books, inventory-constrained quoting, or execution logic. Prefer resources that directly map to (fair → quotes → fills → inventory → risk). citeturn49search0turn49search5  

Where to draw the line:
- Keep microstructure theory only insofar as it translates into implementable signals and constraints (imbalance/microprice, adverse selection awareness, inventory risk). citeturn49search11turn49search0turn49search5  
- Keep Prosperity 2/3 strategies primarily as **design patterns and engineering templates**, not as a “meta” that guarantees the same edges in Prosperity 4. citeturn44view0turn46search2turn41view0turn16view0