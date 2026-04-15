# Official Log Simulator Analysis

Date: 2026-04-15

Scope: Official IMC backtester logs provided for four Round 1 submissions:

- `111005.zip` -> `round1_candidate_v2.py`
- `128697.zip` -> close predecessor of `round1_overhaul_v8.py`
- `130027.zip` -> `round1_overhaul_v14.py`
- `132313.zip` -> `round1_overhaul_v22.py`

## What The Official Logs Actually Give Us

The hosted `.log` payload is richer than the `.json` summary:

- `activitiesLog`
  - per-timestamp book snapshots
  - per-product running PnL
- `tradeHistory`
  - all submission trades
  - non-submission trades where buyer and seller are empty strings
- `logs`
  - per-timestamp lambda/sandbox logs, empty in the supplied runs

This is enough to infer several useful simulator behaviors without inspecting local fill code.

## Grounded Observations

### 1. `activitiesLog` is effectively a pre-submission book snapshot

This is supported by repeated official trades occurring at prices that are inside the displayed spread at the same timestamp.

Example pattern in official Ash:

- visible book at timestamp `t`: `bid1=9993`, `ask1=10011`
- submission trade at `9994`

That means the trade could not have crossed the displayed ask. The most plausible explanation is:

1. the log shows the book before our orders are processed,
2. our quote is inserted inside the spread,
3. a bot trades against it within the same iteration.

This matters because it means official logs can distinguish:

- aggressive takes of displayed liquidity,
- passive inside-spread fills on our quotes,
- and passive joins at displayed prices.

### 2. Pepper is not the source of the later official improvements

Official final product PnL:

| Run | Trader | Ash | Pepper | Total |
| --- | --- | ---: | ---: | ---: |
| `111005` | `candidate_v2` | `2883.8125` | `4256.25` | `7140.0625` |
| `128697` | pre-`v10` Pepper-heavy branch | `2731.34375` | `7426.0` | `10157.34375` |
| `130027` | `v14` | `2715.71875` | `7426.0` | `10141.71875` |
| `132313` | `v22` | `3178.53125` | `7426.0` | `10604.53125` |

The hosted Pepper sleeve is effectively unchanged from `128697` onward.

The `v14 -> v22` official improvement is entirely Ash.

### 3. Official Ash has two distinct monetization channels

#### A. Passive inside-spread capture

For `v22`, official Ash passive-inside fills had:

- `passive_inside_buy`: `n=28`, `qty=155`, `markout_h10=7.143`, `next_mid_h10=-0.268`
- `passive_inside_sell`: `n=28`, `qty=161`, `markout_h10=7.536`, `next_mid_h10=0.179`

Interpretation:

- the next mid barely moves,
- but the realized markout is still strongly positive,
- so the edge is mostly spread capture rather than directional follow-through.

This is an important hosted fact:

- Ash bots are willing to hit one-tick-inside quotes,
- and those fills are not strongly adverse on the next few ticks.

#### B. Aggressive take-and-reset

For `v22`, official Ash takes had:

- `take_a1`: `n=11`, `qty=69`, `markout_h10=1.409`, `next_mid_h10=4.182`
- `take_b1`: `n=10`, `qty=69`, `markout_h10=1.6`, `next_mid_h10=4.1`

Interpretation:

- direct markout after paying the spread is smaller than passive inside fills,
- but the next displayed book moves favorably,
- so these trades appear to exploit stale or reset-prone displayed liquidity.

The hosted Ash sleeve should therefore be thought of as:

- spread capture via inside quotes,
- plus selective stale-quote harvesting via aggressive takes.

### 4. Hosted Ash strongly prefers inside quotes over passive joins

Replay of `round1_overhaul_v22.py` against the official snapshots suggests:

- Ash `passive_inside_buy`: many attempts, non-zero fill rate, good realized economics
- Ash `passive_inside_sell`: many attempts, non-zero fill rate, good realized economics
- Ash `passive_join_sell`: effectively zero fills in this official run
- Ash `passive_join_buy`: extremely sparse fills

This does not mean join quotes are useless in principle, but it does mean the hosted exchange response appears much more favorable to one-tick-inside Ash quoting than to simply waiting at the displayed best.

### 5. Hosted Pepper does not look like an inside-quote market

Replay + official trade classification for `v22`:

- most Pepper action is still aggressive `take_a1` or `take_b1`
- Pepper passive-inside fills are extremely rare
- Pepper passive join fills are essentially absent

This supports the current interpretation:

- Pepper is a carry / recycle product on official,
- not a rich passive market-making product.

## Why `v22` Beat `v14` Officially

The hosted delta from `v14` to `v22` is explained by better Ash monetization, not by a new hidden-product story.

Key changes reflected in the logs:

- same Pepper result
- same Ash aggressive take profile
- better Ash passive-inside execution quality
- more Ash sell quantity realized inside the spread

Most important official delta:

- `v14` `passive_inside_buy` Ash `markout_h10=5.679`
- `v22` `passive_inside_buy` Ash `markout_h10=7.143`

and

- `v14` `passive_inside_sell` Ash `qty=145`, `markout_h10=6.808`
- `v22` `passive_inside_sell` Ash `qty=161`, `markout_h10=7.536`

## Current Opportunity Map

### Highest-confidence opportunity

Improve hosted Ash quote translation further:

- concentrate more passive Ash size where one-tick-inside fills are historically accepted,
- avoid wasting too much passive size on join/deeper quotes that official rarely fills,
- preserve selective aggressive takes when the book looks stale and reset-prone.

### Lower-confidence opportunity

Pepper official may still admit recycle improvements, but the current logs do **not** show a new passive microstructure edge there. Pepper research should remain focused on:

- carry timing,
- recycle timing,
- and generalization of the generator,

not on hosted passive fill farming.

## New Tooling Added

### `prosperity_rust_backtester/scripts/analyze_official_logs.py`

Purpose:

- parse official zip bundles directly
- classify submission trades by mechanism
- compute markouts and next-book response
- optionally replay a local trader file against the official snapshots to infer intended-vs-filled order classes

Example usage:

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py \
  /Users/tahakhan/Downloads/130027.zip \
  /Users/tahakhan/Downloads/132313.zip
```

Replay usage:

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py \
  /Users/tahakhan/Downloads/132313.zip \
  --replay-trader prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v22.py
```

### Official probe submissions

- `prosperity_rust_backtester/trader_archive/Round1/probes/round1_probe_ash_microstructure_v1.py`
- `prosperity_rust_backtester/trader_archive/Round1/probes/round1_probe_pepper_microstructure_v1.py`

These are not ship candidates. They are controlled experiments for the official backtester.

#### Ash probe goals

- compare `bid+1` / `ask-1` inside quoting to `bid+2` / `ask-2`
- compare aggressive takes to passive joins
- estimate which hosted Ash order types get filled and what happens next

#### Pepper probe goals

- test whether Pepper inside quotes ever get hit reliably on official
- compare small aggressive actions to passive joins / inside quotes
- estimate whether hosted Pepper has any overlooked microstructure edge beyond carry

## How To Use The Probe Cycle

1. Run one or both probe traders on the official IMC backtester.
2. Send back the returned zip bundles.
3. Analyze them with:

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py \
  /path/to/probe_zip.zip \
  --replay-trader prosperity_rust_backtester/trader_archive/Round1/probes/round1_probe_ash_microstructure_v1.py
```

or

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py \
  /path/to/probe_zip.zip \
  --replay-trader prosperity_rust_backtester/trader_archive/Round1/probes/round1_probe_pepper_microstructure_v1.py
```

4. Use the fill summary plus trade markouts to answer:

- which order classes are actually accepted officially,
- whether offset `1` or offset `2` is the better Ash passive quote,
- whether official Pepper ever rewards passive inside quoting,
- and whether our own trades change the next displayed book in a monetizable way.

## Guardrail

The current official evidence supports a better hosted Ash execution model.

It does **not** support:

- a new exact Pepper curve fit,
- a claim that hosted Pepper is now a passive MM product,
- or a broad hidden-pattern story in Ash.

The clean next step is probe-driven official microstructure learning, followed by an Ash-only execution revision if the probes confirm higher-confidence hosted fill behavior.
