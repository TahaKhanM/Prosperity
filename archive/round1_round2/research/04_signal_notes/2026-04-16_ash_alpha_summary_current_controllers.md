# Round 1 Ash Alpha Summary

Date: 2026-04-16

Scope:
- product: `ASH_COATED_OSMIUM`
- implementation references:
  - `prosperity_rust_backtester/traders/Round1/Ash.py`
  - `prosperity_rust_backtester/traders/Round1/work/ash/ash_controller_v1.py`
  - `prosperity_rust_backtester/traders/Round1/work/ash/ash_controller_v2.py`
  - `prosperity_rust_backtester/traders/Round1/work/ash/ash_controller_v3.py`
- data-backed research references:
  - `~/Downloads/deep-research-report.md`
  - `prosperity-research/04_signal_notes/latest_signal_ranking.md`
  - `prosperity-research/05_execution_risk/latest_execution_risk_report.md`
  - `prosperity-research/06_validation/latest_validation_report.md`

## What This File Is

This is a compact inventory of the Ash alpha families that the current codebase is trying to monetize.

It is not a claim that every one of these alphas is already realized well in production.
Several are only partially expressed, and the recent validation work shows that the new controllers still do not beat the current `Ash.py` baseline robustly.

The useful distinction is:

- **alpha family**: a repeatable directional or execution edge visible in the data
- **expression layer**: how the trader tries to monetize that edge

## Source Boundary

### Data-backed conclusions

The following are strongly supported by the replay and repo notes:

- Ash is still anchored around `10000`
- short-horizon mean reversion is real
- post-spike fade is real
- top-of-book imbalance and microprice gap matter
- spread alone is weak as a directional predictor
- passive inside fills are much better than crossed fills on average
- one-sided books, especially ask-only books, are strong directional states
- cheap/rich anchor deviation only becomes a strong directional alpha when it aligns with book pressure

### Important caution

The new files `ash_controller_v1.py`, `ash_controller_v2.py`, and `ash_controller_v3.py` were attempts to express these alphas more explicitly, but recent benchmarking showed they were still weaker than `Ash.py`.

So this file summarizes:

- what alpha is present in the data
- how the current strategies attempt to capitalize it
- where the current expression is still incomplete

## Alpha Families We Are Capitalizing

## 1. Neutral Anchor Mean Reversion Around `10000`

### Data signal

- Ash is a stationary / anchored market around `10000`
- rich states tend to drift back down
- cheap states tend to drift back up

### How it is monetized

- `Ash.py` uses an anchored fair blended with dynamic book information
- `ash_controller_v1.py`, `ash_controller_v2.py`, and `ash_controller_v3.py` all preserve the same anchor-centered fair engine
- neutral states are monetized mainly through passive market making rather than aggressive directional taking

### Main action expression

- passive two-sided maker
- inventory-aware skew around anchored fair

### Notes

- this is the base Ash hypothesis
- it is real, but not the highest-value standalone alpha family

## 2. Short-Horizon Fade / Post-Spike Reversion

### Data signal

- one-step and short multi-step Ash moves mean-revert strongly
- post-spike fade is one of the cleanest Ash edges in the repo notes

### How it is monetized

- `Ash.py` includes `ret1` in fair construction through the fade term
- shock detection also changes taker aggressiveness
- the newer controllers still keep the fade term inside the fair engine, even though they change the action-selection layer

### Main action expression

- slightly better fair-value placement after a short move
- selective fade-taking in favorable states
- less aggressive crossing in shocky but weak-confirmation states

### Notes

- this alpha is present in all current Ash implementations
- it is still mostly expressed indirectly through fair and gating, not as a separate explicit spike-fade state machine

## 3. Top-Of-Book Imbalance Alpha

### Data signal

- best-level imbalance has real short-horizon predictive value
- book pressure is materially more informative than spread alone

### How it is monetized

- `Ash.py` uses top-level imbalance directly in buy-follow and sell-follow gates
- `ash_controller_v1.py`, `ash_controller_v2.py`, and `ash_controller_v3.py` use top imbalance inside `ash_fair_context(...)` and in state selection

### Main action expression

- one-sided buy or sell promotion when imbalance aligns with cheap/rich state
- passive quote suppression on the weak side
- occasional small crosses in very strong states

### Notes

- imbalance alone is not treated as enough
- the strategies mostly use it as directional confirmation

## 4. Microprice Gap Alpha

### Data signal

- microprice minus mid has real directional information
- it works best as tactical confirmation rather than as a standalone fair rewrite

### How it is monetized

- all current Ash files use `microprice(...)`
- `Ash.py` uses microprice both in fair construction and medium-spread buy/sell-follow logic
- `ash_controller_v1.py`, `ash_controller_v2.py`, and `ash_controller_v3.py` feed micro-gap into the pressure signal and into state alignment

### Main action expression

- directional confirmation for buy-follow and sell-follow
- slightly better passive quote placement
- selective cross permission when micro-gap is strongly aligned

### Notes

- this is not being used as a giant permanent directional tilt
- it is being used as a short-horizon execution / state feature

## 5. Anchor Deviation × Book Pressure Interaction

### Data signal

- cheap/rich anchor deviation by itself is weaker than the interaction
- the strongest two-sided directional states are:
  - very cheap + buy-lean
  - very rich + sell-lean

### How it is monetized

- `Ash.py` encodes this through medium-spread `buy_follow_signal` and `sell_follow_signal`
- `ash_controller_v1.py` promotes these into `cheap_follow_buy` and `rich_follow_sell`
- `ash_controller_v2.py` makes them first-class discrete states
- `ash_controller_v3.py` uses them as buckets that choose between passive one-sided and cross actions

### Main action expression

- suppress opposite quote
- post one-sided inside quote
- allow small selective crossing when the state is strong enough

### Notes

- this is one of the most important Ash alpha families in the data
- the baseline still under-expresses it, especially on the sell side

## 6. One-Sided Book Continuation

### Data signal

- bid-only books are strong continuation-buy states
- ask-only books are strong continuation-sell states
- ask-only is the clearest under-monetized Ash state in the research

### How it is monetized

- `Ash.py` only captures one-sidedness indirectly and weakly
- `ash_controller_v1.py` adds explicit `bid_only_buy` and `ask_only_sell`
- `ash_controller_v2.py` adds `bid_only_continue_buy` and `ask_only_continue_sell`
- `ash_controller_v3.py` adds `bid_only` and `ask_only` buckets, then chooses passive or aggressive expression from those states

### Main action expression

- default to one-sided quoting
- suppress the opposite side
- size up moderately if inventory is not already stretched

### Notes

- this is the most obvious new alpha family the redesigned controllers were trying to capture
- current validation says the idea is right, but the expression layer still was not robust enough to beat `Ash.py`

## 7. Imbalance Persistence / Short Motif Alpha

### Data signal

- the useful Ash directional states often last more than one tick
- repeated buy-lean or sell-lean sequences matter more than isolated single-tick imbalance

### How it is monetized

- `Ash.py` mostly does not model persistence explicitly
- `ash_controller_v1.py`, `ash_controller_v2.py`, and `ash_controller_v3.py` add:
  - `buy_run`
  - `sell_run`
  - `up_run`
  - `down_run`

### Main action expression

- stronger confidence for follow states
- stronger one-sided promotion when pressure persists
- more selective crossing when persistent pressure aligns with anchor deviation

### Notes

- this alpha family is only present in the newer controllers
- it is one of the main ways those controllers are materially different from `Ash.py`

## 8. Passive-Inside Execution Alpha

### Data signal

- passive inside buys and sells have much better average signed markout than crossed trades
- passive inside is a real Ash execution alpha, not just filler activity

### How it is monetized

- `Ash.py` prefers passive inside capture widely, especially in wider spreads
- `ash_controller_v1.py`, `ash_controller_v2.py`, and `ash_controller_v3.py` keep passive posting as the default in neutral states
- the newer controllers try to keep passive as the default high-quality action, then only escalate when state strength is high

### Main action expression

- inside one-tick passive quotes
- two-sided passive maker in neutral states
- one-sided passive follow in aligned states

### Notes

- this is still the core monetization engine of Ash
- the key problem is not that passive is bad
- the key problem is deciding when passive should give way to one-sided or crossed action

## 9. State-Dependent Passive vs Aggressive Selection

### Data signal

- aggressive trades are positive on average, but materially worse than passive inside fills
- some states are strong enough that waiting is the bigger leak

### How it is monetized

- `Ash.py` uses narrow taker and recycler logic, mostly through medium-spread gates
- `ash_controller_v1.py` only crosses in strong cheap-follow / rich-follow or inventory-emergency states
- `ash_controller_v2.py` uses discrete states and allows selective crosses only in stronger follow states
- `ash_controller_v3.py` makes this most explicit by scoring:
  - passive two-sided
  - passive buy
  - passive sell
  - cross buy
  - cross sell
  - hold

### Main action expression

- rare, small crosses in strong aligned states
- otherwise passive one-sided or passive two-sided
- hold / stand-down when the state is weak or ambiguous

### Notes

- this is a real alpha family, but mainly an execution-selection alpha, not a market-direction alpha
- `ash_controller_v3.py` is the cleanest attempt to encode it

## 10. Inventory-Conditioned Recycling

### Data signal

- local Ash runs carry too much inventory under conservative matching
- hosted evidence suggests high inventory should be managed more tightly
- recycling is valuable, but only when the directional state has weakened

### How it is monetized

- `Ash.py` has inventory recycle and clear logic, but it is fairly coarse
- `ash_controller_v1.py` adds explicit `recycle_long` and `recycle_short` states
- `ash_controller_v2.py` also adds explicit recycle states with more one-sided cleanup
- `ash_controller_v3.py` bakes recycling into the action selector and bucket system

### Main action expression

- inventory-based passive one-sided flattening
- occasional cross to reduce stretched inventory
- size suppression when already too long or too short

### Notes

- inventory is not treated as the main directional alpha
- it is treated as a state suppressor and execution risk controller

## 11. Wide Spread As Passive Economics, Not Direction

### Data signal

- wide spread by itself is weakly predictive for direction
- wide spread is useful mainly because passive economics improve there

### How it is monetized

- `Ash.py` uses wide spread mostly to favor passive inside capture
- the newer controllers inherit the same idea indirectly through passive price placement and state-driven one-sided promotion

### Main action expression

- better passive quote placement in wider books
- more room for one-sided passive posting

### Notes

- this is not a primary directional alpha
- it is an execution regime that improves monetization of other signals

## 12. Join-Order Removal As Execution Hygiene

### Data signal

- join orders were dead capital in the replay evidence

### How it is monetized

- `Ash.py` still contains join-like behavior in its maker template
- the newer Ash controllers were designed around passive inside, one-sided passive, or selective crossing, not around join-order farming

### Main action expression

- avoid spending quote slots on low-value join placements

### Notes

- this is not a market alpha
- it is a way to stop diluting real alpha with useless quote types

## Controller-by-Controller View

| Alpha family | `Ash.py` | `ash_controller_v1.py` | `ash_controller_v2.py` | `ash_controller_v3.py` |
| --- | --- | --- | --- | --- |
| Anchor mean reversion | strong | strong | strong | strong |
| Post-spike fade | medium | medium | medium | medium |
| Imbalance + microprice confirmation | strong | strong | strong | strong |
| Cheap/rich × pressure interaction | medium | strong | strong | strong |
| One-sided books | weak | strong | strong | strong |
| Imbalance persistence | weak | medium | medium | medium |
| Passive-inside execution alpha | strong | strong | strong | strong |
| Passive vs aggressive selector | weak | medium | medium | strong |
| Inventory-conditioned recycle | medium | medium | medium | medium |
| Join-order removal / de-emphasis | weak | strong | strong | strong |

## What We Are Not Treating As Primary Alpha

- spread alone
- generic medium-spread threshold tuning
- broad fair-value coefficient retuning
- anchor extremes with flat imbalance as directional states
- broad passive suppression

These were either weak in the data or already shown to be too small / too fragile to be the main Ash upside.

## Bottom Line

The current Ash work is capitalizing five genuinely important data-backed families:

1. anchor-based mean reversion,
2. short-horizon fade,
3. imbalance and microprice pressure,
4. cheap/rich anchor deviation aligned with book pressure,
5. passive-inside execution edge.

The newer controller files then try to add three more under-monetized families more explicitly:

1. one-sided book continuation,
2. imbalance persistence,
3. explicit passive-vs-aggressive state selection.

That is the real Ash alpha stack in the current work.

The unresolved problem is not “find another signal.”
It is “express the right existing signals with the right state-to-action mapping so the edge transfers under conservative execution.”
