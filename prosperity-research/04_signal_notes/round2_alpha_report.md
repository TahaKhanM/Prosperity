# Round 2 Alpha Report

Date: 2026-04-19

Scope: deep alpha search for Round 2 on `ASH_COATED_OSMIUM` and
`INTARIAN_PEPPER_ROOT`, with explicit separation between predictive signal,
monetizable edge, and implementation-ready strategy families.

Evidence surface used:

- official context and repo assumptions:
  [current_assumptions.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/01_assumptions/current_assumptions.md)
- analyzer audit:
  [round2_analyzer_audit.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_analyzer_audit.md)
- per-round analyzer snapshots:
  - [round1 snapshot](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/ai_strategy_context_by_round/round1/strategy_brief.md)
  - [round2 snapshot](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/ai_strategy_context_by_round/round2/strategy_brief.md)
- carryover tables:
  [round2_carryover_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_carryover_report.md)
- durable registry:
  [round2_alpha_registry.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_alpha_registry.md)

## Executive Read

- `ASH_COATED_OSMIUM` is the stable product. The core Round 2 edge is still an
  anchored fair + passive/event-reversion structure. The edge is structural,
  but the monetization is execution-sensitive and not obviously taker-led.
- `INTARIAN_PEPPER_ROOT` is the real Round 2 opportunity. It remains a drifting
  fair product, but the residual mean-reversion and fair-deviation signals are
  much stronger, cleaner, and more monetizable than in Round 1.
- The best next implementation work should be Pepper-first, with Ash kept as a
  disciplined anchored sleeve rather than a complexity sink.

## Product Classification

| Product | Round 2 classification | Working market model | Confidence |
|---|---|---|---|
| `ASH_COATED_OSMIUM` | `STABLE` | anchored replenishing-maker market with spike-fade and execution-state overlays | high |
| `INTARIAN_PEPPER_ROOT` | `DRIFTING` | moving-fair residual mean-reversion market with inventory-aware taking and microstructure skew | high |

## ASH_COATED_OSMIUM

### High-confidence edges

1. Anchored fair with passive/value-based quoting.
   Evidence: classification and top signals are nearly unchanged vs Round 1;
   `wall_delta`, `imb_l1`, `z20`, `ret1`, and `micro_delta` all remain strong
   and sign-stable.

2. Spike fade overlay.
   Evidence: spike reversion remains confirmed in Round 2 even though spike
   frequency is lower than in Round 1.

3. Small fair-proxy improvement from `mm_mid` to `wall_mid`.
   Evidence: fair-proxy comparison flips the best proxy by a small but real
   margin in Round 2.

### Medium-confidence hypotheses

1. Medium-spread action cleanup.
   Rationale: prior repo execution work says the only transfer-shaped Ash gains
   came from suppressing bad medium-spread takers, and Round 2 still offers no
   clear evidence that aggressive taking is the right primary monetization path.

2. Earlier flatten / narrower passive participation.
   Rationale: consistent with the anchored shell and likely safer than trying to
   invent new Ash signal complexity.

### Weak or rejected ideas

1. Standalone OFI.
   Evidence: weak in both rounds.

2. Trend-following Ash.
   Evidence: both rounds remain strongly mean reverting.

3. “Take-first Ash” as the main architecture.
   Evidence: analyzer execution summary shows no robust cross-book taking edge
   despite strong predictive structure.

### Monetization view

Ash is a product where prediction is easier than extraction. The structural
edge is real, but it should be monetized through:

- anchored market making,
- fair-relative passive placement,
- spike/event fades,
- inventory-aware recycling,
- selective action suppression in weak execution states.

## INTARIAN_PEPPER_ROOT

### High-confidence edges

1. Dynamic-fair residual mean reversion.
   Evidence: Pepper stays `DRIFTING`, but lag-1 ACF shifts from neutral in
   Round 1 to `-0.4947` in Round 2, while `z20` becomes the dominant and stable
   signal.

2. Fair-deviation taking around a moving fair.
   Evidence: `wall_delta` and `mm_delta` strengthen from weak Round 1 hints to
   strong, stable Round 2 signals; buy/sell take markouts stay positive.

3. Inventory-aware recycle shell.
   Evidence: Round 2 take-only sim still reaches the hard limit, but less often
   than Round 1; inventory control is still needed, just less desperately.

4. Imbalance / microprice skew as secondary overlay.
   Evidence: `imb_l1`, `imbalance`, and `micro_delta` all strengthen materially
   and stay sign-consistent.

### Medium-confidence hypotheses

1. Fill-quality / EV-per-quote gating.
   Rationale: repo research repeatedly says the remaining Pepper edge is quote
   selection rather than a better base signal; this fits the Round 2 structure,
   but it is not directly proven by the raw-data analyzer alone.

2. Regularised template or drift-test fallback.
   Rationale: a smoothed moving fair likely helps, but exact curve hardcoding is
   still too overfit-prone.

3. Spike fade as a secondary overlay.
   Rationale: spike reversion exists, but the base dynamic-fair residual edge is
   clearly stronger.

### Weak or rejected ideas

1. Exact Pepper session path hardcoding.
   Reason: this is the clearest overfit family.

2. Standalone OFI.
   Reason: still weak and sign-flippy.

3. Fixed-fair Pepper.
   Reason: daily drift persists across both rounds.

### Monetization view

Pepper is the product where prediction and monetization align best in Round 2.
The core monetization path is:

- take when price deviates from the moving fair,
- clear aggressively as the fair catches up,
- use imbalance/microprice for skew and side choice,
- cap inventory before the residual edge turns into passive drift exposure.

## Structural Vs Noisy Edges

### Structural / reusable

- Ash anchored fair and fair-deviation reversion
- Ash spike fade
- Pepper moving fair
- Pepper residual/z-score reversion
- Pepper fair-deviation taking
- Pepper inventory-aware recycle shell

### Small but real overlays

- Ash imbalance-side quote bias
- Ash spread-change state filter
- Pepper imbalance / microprice skew
- Pepper spike overlay

### Noisy or overfit-prone

- standalone OFI in either product
- exact path hardcoding for Pepper
- trend-following Ash
- deeper passive-layer expansion for Ash without stronger execution evidence

## Round 2 Prioritisation

1. `INTARIAN_PEPPER_ROOT` deserves the main implementation budget.
   The structural edge is stronger, the monetization is clearer, and the
   carryover tables show a genuine Round 2 strengthening rather than mere
   persistence.

2. `ASH_COATED_OSMIUM` should stay simple.
   The product is stable, but the remaining work is mostly execution quality and
   risk control, not a new signal family.

3. Complexity should enter Pepper before Ash.
   The likely remaining Pepper upside is in better action selection or quote
   gating. The likely Ash upside is smaller and easier to overfit.

## What Should Be Tested Next In Code

1. A Pepper dynamic-fair residual trader with a soft inventory cap and
   imbalance-aware skew.
2. An Ash anchored maker with only modest Round 2-specific retuning:
   `wall_mid` fair, spike fade, and tighter action suppression in weak states.
3. If Pepper still leaves unexplained slippage, add a quote-EV gate rather than
   another new base signal.
