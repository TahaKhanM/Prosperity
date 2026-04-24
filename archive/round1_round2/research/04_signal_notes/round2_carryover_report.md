# Round 1 ↔ Round 2 Carryover Report

Date: 2026-04-19

Scope: compare Round 1 and Round 2 for `ASH_COATED_OSMIUM` and
`INTARIAN_PEPPER_ROOT`, determine what carries over, and separate structural
carryover from ideas that require retuning or rejection.

Supporting tables:

- [round2_round_comparison_metrics.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_round_comparison_metrics.csv)
- [round2_fair_proxy_comparison.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_fair_proxy_comparison.csv)
- [round2_signal_carryover_matrix.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_signal_carryover_matrix.csv)
- Analyzer snapshots:
  - [round1 snapshot](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/ai_strategy_context_by_round/round1/strategy_brief.md)
  - [round2 snapshot](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/ai_strategy_context_by_round/round2/strategy_brief.md)

## Product-Level Verdict

| Product | Round 1 summary | Round 2 summary | Product-level carryover verdict |
|---|---|---|---|
| `ASH_COATED_OSMIUM` | Stable anchored fair, strong short-horizon reversion, spike fade, limited evidence for direct taking | Same structure persists almost unchanged; fair proxy shifts slightly toward `wall_mid`; spike reversion still present | `carries over directly` |
| `INTARIAN_PEPPER_ROOT` | Drifting fair idea present, but signal strength is weak/uneven and mostly concentrated in one day | Dynamic-fair mean reversion becomes strong, stable, and monetizable; inventory pressure is lower despite stronger edge | `carries over with major retuning` |

## Side-By-Side Core Metrics

| Product | Best fair R1 | Best fair R2 | Lag-1 ACF R1 | Lag-1 ACF R2 | Best signal corr R1 | Best signal corr R2 | Sim `% at limit` R1 | Sim `% at limit` R2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `ASH_COATED_OSMIUM` | `mm_mid` | `wall_mid` | `-0.4937` | `-0.4818` | `+0.5881` | `+0.5876` | `0.0` | `0.0` |
| `INTARIAN_PEPPER_ROOT` | `wall_mid` | `mm_mid` | `-0.0072` | `-0.4947` | `-0.0704` | `-0.6371` | `22.45` | `7.37` |

Interpretation:

- Ash is the clean carryover product. Nearly every top-level metric is stable.
- Pepper keeps the same broad `drifting fair` classification, but the actual
  exploitable structure changes materially. Round 2 is not just “Round 1 but a
  bit stronger”; it is a cleaner residual mean-reversion market.

## ASH_COATED_OSMIUM Carryover

### What carries over directly

| Family | Round 1 evidence | Round 2 evidence | Verdict |
|---|---|---|---|
| Product classification | `STABLE`, `fixed_fair_mm` | `STABLE`, `fixed_fair_mm` | `carries over directly` |
| Mean reversion | lag-1 ACF `-0.4937` | lag-1 ACF `-0.4818` | `carries over directly` |
| Fair-deviation edge | `wall_delta`, `mm_delta`, `z20`, `imb_l1` all strong | same ranking and sign stability | `carries over directly` |
| Spike fade | spike reversion confirmed | spike reversion confirmed | `carries over directly` |
| No cross-product dependency | no notable correlation | no notable correlation | `carries over directly` |

### What carries over with retuning

| Family | Why retuning is needed |
|---|---|
| Fair proxy choice | `mm_mid` narrowly wins in Round 1; `wall_mid` narrowly wins in Round 2. The anchored-fair family survives, but the best proxy changes by a small margin. |
| Spread-change overlay | weak in Round 1, somewhat stronger in Round 2. Useful only as a secondary state filter, not as a primary signal. |

### What does not carry over or should stay rejected

| Family | Why rejected |
|---|---|
| Standalone OFI directional alpha | weak in both rounds; sign noise and near-zero signal |
| Trend-following Ash fair drift | both rounds are strongly mean reverting |
| Cross-book taker-first Ash strategy | analyzer execution summary shows no robust direct-take opportunity in either round; monetization looks passive/event-driven instead |

### Ash conclusion

Round 1 Ash findings are mostly valid in Round 2. The right mental model remains:

- anchored fair,
- short-horizon reversion,
- spike fade as overlay,
- inventory-aware passive quoting,
- avoid inventing a more directional Ash story than the data supports.

The main Round 2 Ash change is not market structure; it is that `wall_mid`
edges slightly out `mm_mid` as the best fair proxy.

## INTARIAN_PEPPER_ROOT Carryover

### What carries over directly

| Family | Round 1 evidence | Round 2 evidence | Verdict |
|---|---|---|---|
| Product classification | `DRIFTING` | `DRIFTING` | `carries over directly` |
| Dynamic fair vs fixed fair | daily means shift by about `1000/day` | daily means shift by about `999/day` | `carries over directly` |
| Spike reversion exists | reversion confirmed | reversion confirmed | `carries over directly` |

### What carries over with major retuning

| Family | Round 1 evidence | Round 2 evidence | Verdict |
|---|---|---|---|
| `z20` / residual mean reversion | weak overall (`-0.0704`) and day-concentrated | dominant signal (`-0.6371`) and stable across days | `carries over with major retuning` |
| `wall_delta` / `mm_delta` fair residuals | weak overall (`~+0.07`) | strong and stable (`+0.538` to `+0.573`) | `carries over with major retuning` |
| `imb_l1` / micropressure overlays | weak but same sign | much stronger, stable secondary overlay | `carries over with retuning` |
| Inventory cap / recycle logic | Round 1 take-only sim pins at limit `22.45%` of ticks | Round 2 still needs inventory control, but the same shell is far less stressed at `7.37%` | `carries over with retuning` |

### What does not carry over directly

| Family | Why |
|---|---|
| Weak/neutral Round 1 Pepper baseline conclusions | Round 2 is much more strongly mean reverting and much more monetizable; Round 1 underestimates how tradable Pepper becomes |
| Fixed-fair Pepper logic | daily drift in both rounds rejects a fixed anchor |
| Standalone OFI alpha | weak/noisy in both rounds, with sign-flip risk still present |

### Pepper conclusion

Only the high-level “Pepper needs a moving fair” idea carries over cleanly.
Most of the actionable Round 2 Pepper edge is much stronger than Round 1 and
should be treated as a new parameter regime rather than a small retune of a
Round 1 controller.

The practical implication is:

- keep the moving-fair mental model,
- promote residual mean reversion and fair-deviation taking to first-class
  strategy components,
- treat microstructure overlays as helpers,
- reject exact Round 1 threshold transfer.

## Signal Carryover Summary

### Ash

- `wall_delta`, `imb_l1`, `mm_delta`, `z20`, `micro_delta`, and `ret1` all
  carry over directly.
- `spread_chg` strengthens slightly in Round 2 but remains secondary.
- `ofi_5` is weak in both rounds and should not be promoted.

### Pepper

- `z20`, `wall_delta`, `mm_delta`, and `imb_l1` move from weak or uneven in
  Round 1 to strong and stable in Round 2.
- `ret1` and `micro_delta` are meaningfully stronger in Round 2.
- `ofi_5` remains weak and unstable.

## Carryover Classification By Major Idea

| Product | Idea | Verdict | Why |
|---|---|---|---|
| `ASH_COATED_OSMIUM` | anchored fair + passive making | `carries over directly` | structure, spread, and reversion are almost unchanged |
| `ASH_COATED_OSMIUM` | spike-fade overlay | `carries over directly` | spike reversion survives with slightly lower frequency |
| `ASH_COATED_OSMIUM` | fair proxy selection | `carries over with retuning` | `mm_mid` to `wall_mid` flip is small but real |
| `ASH_COATED_OSMIUM` | standalone OFI | `does not carry over` | weak in both rounds |
| `INTARIAN_PEPPER_ROOT` | moving fair | `carries over directly` | daily drift remains the defining feature |
| `INTARIAN_PEPPER_ROOT` | residual/z-score mean reversion | `carries over with retuning` | becomes much stronger and more stable in Round 2 |
| `INTARIAN_PEPPER_ROOT` | fair-deviation taking | `carries over with retuning` | same family, much larger and cleaner edge |
| `INTARIAN_PEPPER_ROOT` | inventory-cap / recycle shell | `carries over with retuning` | still needed, but Round 2 inventory pressure is materially lower |
| `INTARIAN_PEPPER_ROOT` | exact Round 1 threshold reuse | `does not carry over` | signal strength and execution profile changed too much |
| `INTARIAN_PEPPER_ROOT` | standalone OFI | `does not carry over` | weak and unstable in both rounds |

## Final Carryover Verdict

- `ASH_COATED_OSMIUM`: Round 1 conclusions mostly survive. Keep the anchored
  fair + passive/event-reversion worldview.
- `INTARIAN_PEPPER_ROOT`: only the broad moving-fair worldview survives cleanly.
  Round 2 requires a fresh calibration and should be treated as a stronger,
  cleaner residual mean-reversion market than Round 1.
