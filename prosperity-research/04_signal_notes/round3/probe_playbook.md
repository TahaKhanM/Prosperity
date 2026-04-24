# IMC Backtester Probe Playbook — Round 3

**Status:** active research artifact. Last reviewed 2026-04-25.

## Why this exists

Our local Python (`imc-prosperity-4-backtester/`) and Rust
(`prosperity_rust_backtester/`) backtesters have been unreliable for Round 3
relative to the official IMC engine. Rather than guess the divergence, we
run a deterministic probe trader that submits schema-narrow, tightly-timed
experiments across one submission day. The official engine's responses —
captured in the hosted run's `tradeHistory` and `lambdaLog` — let us
reverse-engineer the matching rules.

## Artifacts

| Path | Purpose |
|------|---------|
| `prosperity_rust_backtester/traders/Round3/probes/probe_v1_matching.py` | The probe trader — one file, no deps. |
| `scripts/probe_run_python.sh` | Run probe on Python backtester. |
| `scripts/probe_run_rust.sh` | Run probe on Rust backtester. |
| `scripts/probe_analyze.py` | 3-way diff of Python / Rust / Official fills keyed by probe ID. |
| `runs/probes/` | All generated outputs (gitignored). |

## Pre-flight checks (CRITICAL — uncovered by v1 probe run)

Before trusting any local backtester result for Round 3, verify both engines
are using current position limits. The first probe run on 2026-04-25 found
two stale-config bugs that silently nerfed every Round 3 product to a
much lower limit than the documented 200 / 300:

1. **Python BT** — the conda env's `prosperity4bt` was installed from an
   older snapshot; its `LIMITS` dict only contained 4 entries, so every
   Round 3 product fell back to `DEFAULT_POSITION_LIMIT = 50`. Fix:

   ```
   /opt/miniconda3/envs/prosperity/bin/pip install -e \
     /Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester/
   ```

   Verify with:
   `python -c "from prosperity4bt.data import LIMITS; print(len(LIMITS), 'VEV_6500' in LIMITS)"`
   — expect `16 True`.

2. **Rust BT** — `cargo_local.sh` redirects builds to
   `~/Library/Caches/rust_backtester/target/`, but `probe_run_rust.sh`
   reads `prosperity_rust_backtester/target/release/rust_backtester`.
   The source-tree binary was last built before the Round 3 limit table
   was added, so it enforced 100 for VEV_6500. Fix:

   ```
   cd prosperity_rust_backtester && bash scripts/cargo_local.sh build --release
   cp ~/Library/Caches/rust_backtester/target/release/rust_backtester \
      target/release/rust_backtester
   ```

   Verify by checking the binary mtime is recent.

These are real Round 3 backtest-fidelity bugs independent of any IMC
divergence; if you saw "the IMC backtester shows much different results"
this is part of the explanation. Document any future installs that drift.

## How to run end-to-end

1. `bash scripts/probe_run_python.sh`  — produces `python_bt_stdout.log` + `python_bt_output.json`.
2. `bash scripts/probe_run_rust.sh`    — produces `rust_bt_stdout.log` + `rust_bt_output.json`.
3. Submit `probe_v1_matching.py` to IMC Prosperity 4 website. Download the run's `.log` (JSON format, same shape as `Official Replays/v4_official_backtest/379811.log`).
4. ```
   python scripts/probe_analyze.py \
     --python-stdout runs/probes/python_bt_stdout.log \
     --python-json   runs/probes/python_bt_output.json \
     --rust-stdout   runs/probes/rust_bt_stdout.log \
     --rust-json     runs/probes/rust_bt_output.json \
     --official-log  path/to/official_submission.log
   ```
5. Read `runs/probes/diff_summary.md` — one section per `eid`, flagging divergences.

## Things to remember before submitting

- **Last submission wins**, so burn a submission slot on this without guilt.
- Probe day is live; we pick day 2 for local comparison because that's the day our one existing official replay (`379811`) was run on.
- The trader is deliberately passive for most ticks (`E00`, `E28` idle, narrow single-tick probes). Expected aggregate PnL is small but may be mildly negative — tolerate it.
- All probe experiments respect documented position limits **except** E12 and E14, which are intentionally designed to trigger rejection. If the engine silently truncates instead, that is a finding.

## Probe catalogue

Each probe logs exactly one line per fire event to stdout:

```
PROBE eid=<id> ts=<T> product=<P> action=<A> orders=<price x qty list>
      book=b=<levels>|a=<levels> pos_before=<n> limit=<n> note=<free>
```

Range probes only log on ticks divisible by 100 to keep logs readable.

### Calibration / sanity probes

| eid | Tick | What we send | Why |
|-----|------|-------------|-----|
| `E00_IDLE_A` | 0–999 | nothing | Baseline that engine produces no SUBMISSION fills without orders. Confirms our stdin/stdout contract is clean. |
| `E28_IDLE_END` | 9000–9999 | nothing | Symmetric final baseline. Also verifies end-of-round settlement does not inject phantom trades. |
| `E01_CROSS_ASK_TOP` | 1000 | HYDROGEL BUY 1 @ best_ask | Simplest fill. Confirms top-of-book match at exactly the ask price. Python & Rust both must fill this. Divergence here means we mis-understand the basic matching priority. |
| `E02_CROSS_BID_TOP` | 1100 | HYDROGEL SELL 1 @ best_bid | Symmetric. |
| `E03_FLATTEN_H` | 1200 | auto-flatten HYDROGEL to 0 | Cleanup. |
| `E04_CROSS_ASK_TOP_VE` | 1400 | VE BUY 1 @ best_ask | Same idea on VELVETFRUIT. |
| `E05_FLATTEN_VE` | 1500 | auto-flatten VE | Cleanup. |

### Waterfall / multi-level probes

| eid | Tick | What we send | Hypothesis |
|-----|------|-------------|------------|
| `E06_WATERFALL_SUM3` | 2000 | HYDROGEL BUY qty = sum of ask volumes at levels 1..3, price = level-3 ask. Capped at 100. | Official engine fills at each level's price as stock depth is consumed. If locals return a single VWAP fill or if they fill at the single submitted price, they diverge. |
| `E07_WATERFALL_EXCESS` | 2100 | HYDROGEL BUY qty = sum_levels + 20, price = level-3 ask + 50 | The 20-unit excess has no book support. Official engine should stop at `sum_levels`. Locals may "invent" liquidity by matching against external historical trades at or below the submitted price. If we see >sum_levels fills locally but = sum_levels officially → **key divergence: locals double-count external trades as fillable liquidity**. |
| `E08_FLATTEN_H` | 2200 | auto-flatten | Cleanup. |

### Resting / passive probes — external trade divergence test

This is the highest-value block. The hypothesis under test:

> Locals treat the `trades_round_3_day_*.csv` historical trades as
> additional counterparty liquidity that our resting orders can fill
> against. The official IMC engine broadcasts those trades (they appear in
> `tradeHistory` as `{buyer: "", seller: ""}`) but does **not** allow them
> to cross with our orders — they are bot↔bot interactions off-book.

If this hypothesis holds, a resting BUY at one tick below best bid should
fill occasionally locally but never officially.

| eid | Tick | What we send | Expected if hypothesis holds |
|-----|------|-------------|------------------------------|
| `E09_RESTING_BELOW_BB` | 3000–3499 | VE BUY 5 @ (best_bid − 1), resubmitted every tick | Local: occasional fills when an external SELL trade occurs at/below that price. Official: **zero fills across 500 ticks**. |
| `E10_RESTING_JOIN_BB` | 3500–3999 | VE BUY 5 @ best_bid, resubmitted every tick | Both: some fills as the bid is hit. Differential fill rate quantifies how much of local fill volume actually comes from shadow external trades. |
| `E24_RESTING_ABOVE_BA` | 7000–7499 | VE SELL 5 @ (best_ask + 1) | Mirror test on the sell side. |
| `E26_WIDE_RESTING_H` | 8000–8499 | HYDROGEL BUY/SELL ±15 ticks from mid | Maximum separation from the book. Any local fills here are almost certainly phantom. |

### Position-limit probes

| eid | Tick | What we send | Hypothesis |
|-----|------|-------------|------------|
| `E12_POSLIMIT_OVER1` | 4200 | VEV_6500 BUY qty = (limit − pos) + 1, crossing price | Per docs, engine rejects ALL orders for that product this tick. Expected: zero fills this tick for VEV_6500. |
| `E13_POSLIMIT_EXACT` | 4300 | VEV_6500 BUY qty = (limit − pos), crossing price | Should be allowed. Fill volume = min(qty, available ask liquidity). |
| `E14_POSLIMIT_AGG` | 4400 | VEV_6500 two BUY orders, each ≈ (limit − pos)/2 + 3, same crossing price | Aggregate exceeds limit by 6. Rule says ALL orders rejected. If a local fills one but not the other → non-conformant aggregation. |
| `E15_FLATTEN_V65` | 4500 | auto-flatten VEV_6500 | Cleanup. |

### Edge-case & schema probes

| eid | Tick | What we send | Hypothesis |
|-----|------|-------------|------------|
| `E16_SELFCROSS` | 5000 | VEV_6500 simultaneous BUY @ ask+5 and SELL @ bid−5, qty 3 each | Self-trade test. Official likely does NOT match our BUY against our own SELL. Fill pattern should match two independent crossings of the external book. |
| `E18_QTY_ZERO` | 5300 | VEV_6500 Order(price=ask, qty=0) | Does the engine silently drop it, raise, or fail the whole tick? |
| `E19_DUPLICATE_BUY` | 5400 | VEV_6500 two BUY orders at same price, qty 2 each | Both should fill if book has ≥4 volume. Tests whether engine aggregates for limit check but matches independently. |
| `E21_PRICE_ZERO_BUY` | 6000 | VEV_6500 BUY 1 @ price=0 | VEV_6500 best ask is typically 1. This order should NEVER cross (0 < 1). Is price=0 accepted at all? |
| `E22_SELL_AT_ZERO` | 6100 | VEV_6500 SELL 1 @ price=0 | best_bid on VEV_6500 is typically 0. Joining the bid at 0. Should fill iff an external BUY crosses at 0 — useful data point on whether price=0 orders even participate. |

### Product flat-keepers

E03, E05, E08, E11, E15, E17, E20, E23, E25, E27 exist purely to return the
position to zero between experiments so each probe runs in a clean state.

## Reading the diff summary

For each `eid`, `probe_analyze.py` emits:

- **Intent** — restated from the probe metadata.
- **Python BT** — fills matching `(eid_symbol, eid_ts_window)` with source = python_bt.
- **Rust BT** — same for rust_bt.
- **Official** — same for official_imc (or "pending" if no log supplied).
- **Divergence tag**:
    - `identical`: all three sources agree on fill count and net qty.
    - `local_over_counts`: locals show more fills than official.
    - `local_under_counts`: rare; locals miss fills that the engine produced.
    - `price_mismatch`: same fill count but VWAP differs.
    - `rejection_visible` / `rejection_hidden`: only relevant for E12/E14.

## What a successful probe run proves

After one submission we expect to settle these questions, in order of
research value:

1. **External-trade liquidity (E07, E09, E24, E26)** — are historical
   `""`/`""` trades available for our orders to match, or purely broadcast
   traffic?  Primary finding; expected to reset local PnL estimates.
2. **Multi-level fill pricing (E06)** — does the engine use per-level
   execution prices or a blended fill price?
3. **Position-limit aggregation (E12, E14)** — is the all-or-nothing
   rejection rule respected exactly, or does the engine partial-clamp?
4. **Self-cross (E16)** — can our BUY and SELL in the same tick cross each
   other?
5. **Schema edge cases (E18, E21)** — do `qty=0` and `price=0` orders
   survive the submission validator?

## Iteration plan

- v1 (this doc) covers matching-engine mechanics.
- v2 should add: conversion-observation probes (Round 3 has none, but
  Round 4+ will); counterparty-name probes (if a named bot appears in any
  round's live `market_trades`, copy-probing); fee/slippage probes with a
  deliberate round-trip at mid to detect per-fill cost.
