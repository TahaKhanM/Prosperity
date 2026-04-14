# Round 1 Signal Ranking

Date: 2026-04-14

Scope: Round 1 signal ranking for `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`, using the official Round 1 files first, then the raw local Round 1 datasets, then older public-repo ideas only as workflow analogy.

Primary sources used:
- `Prosperity Context/Official Prosperity Context.md`
- `Prosperity Context/Official Prosperity Context Round 1.md`
- `Prosperity Context/ROUND1_PROMPT_HINTS_CONTEXT.md`
- `prosperity_rust_backtester/datasets/round1/prices_round_1_day_-2.csv`
- `prosperity_rust_backtester/datasets/round1/prices_round_1_day_-1.csv`
- `prosperity_rust_backtester/datasets/round1/prices_round_1_day_0.csv`
- `prosperity_rust_backtester/datasets/round1/trades_round_1_day_-2.csv`
- `prosperity_rust_backtester/datasets/round1/trades_round_1_day_-1.csv`
- `prosperity_rust_backtester/datasets/round1/trades_round_1_day_0.csv`
- `prosperity-research/03_repo_notes/prosperity3_rank2_repo_research_note.md`
- `prosperity-research/03_repo_notes/prosperity3_research_note.md`
- `prosperity-research/03_repo_notes/chrispyroberts_imc_prosperity_3_research_note.md`
- `Round1AnalysisV1/ai_strategy_context.zip`

Method summary:
- Fair-value tests used only two-sided, non-zero-mid rows.
- Sample size after filtering:
  - `ASH_COATED_OSMIUM`: 27,644 two-sided rows, 1,265 trades
  - `INTARIAN_PEPPER_ROOT`: 27,688 two-sided rows, 1,011 trades
- Estimators tested:
  - `simple mid = (best_bid + best_ask) / 2`
  - `microprice = (ask * bid_vol + bid * ask_vol) / (bid_vol + ask_vol)`
  - `wall mid = midpoint of the largest displayed bid wall and largest displayed ask wall`
  - `filtered market-maker mid (mm10) = midpoint of the best bid and best ask among visible levels with size >= 10, fallback to BBO`
- For `INTARIAN_PEPPER_ROOT`, I also tested a fitted linear intraday trend baseline because the raw data visibly drifts within each day.

## Source Status

### Confirmed by official docs

- Round 1 live products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Both Round 1 position limits are `80`.
- Round 1 also includes an Exchange Auction, but that is separate from this signal note.
- The official round brief frames:
  - `INTARIAN_PEPPER_ROOT` as relatively steady, similar in spirit to tutorial `EMERALDS`
  - `ASH_COATED_OSMIUM` as more volatile, possibly pattern-driven

### Supported by local data

- `ASH_COATED_OSMIUM` is best treated as an anchored / stationary wide-spread market-making product with small book-driven lean and modest short-horizon spike reversion.
- `INTARIAN_PEPPER_ROOT` is not fixed-anchor stable in the sample. It shows a strong deterministic intraday upward drift on all three local days, plus smaller book and trade-pressure overlays.
- Spread state exists, but spread itself is weak as a predictive alpha signal in both products.
- One-sided or empty books are common enough to matter operationally:
  - `ASH_COATED_OSMIUM`: 7.7% of rows
  - `INTARIAN_PEPPER_ROOT`: 7.7% of rows

### Supported only by public analogy

- Use a phased order-construction pattern: take -> clear -> make.
- Use calm quote placement, size discipline, and inventory-aware skew rather than eager crossing on small signals.
- Consider wall-mid / market-maker-mid style fair-value candidates first for market-making products before reaching for heavier models.

### Still unproven

- That the exact local drift shape in `INTARIAN_PEPPER_ROOT` will persist unchanged in live Round 1.
- That spread-regime shifts themselves are a primary alpha source.
- That periodic bot-cycle timing signals are robust enough to trade.
- That quote-wall effects are large enough to monetize directly rather than just use as a weak tie-breaker.

## Product Classification

| Product | Market type | Main fair-value view | Main monetization path | Confidence |
| --- | --- | --- | --- | --- |
| `ASH_COATED_OSMIUM` | Anchored / stationary, wide-spread, mildly book-driven | Anchor around `10000` with book-refined fair via `mm10` or `wall_mid` | Passive spread capture, selective stale-quote taking, small book-skew overlay | High |
| `INTARIAN_PEPPER_ROOT` | Drifting / rolling-fair-value, with secondary directional pressure | Time-aware rolling fair, then refine with `wall_mid` or `microprice` | Passive market making around a rising fair, upward skew, selective takes against stale offers | High |

## Fair-Value Estimator Tests

Average MAE versus future mid on horizons `1`, `5`, `10` ticks:

### `ASH_COATED_OSMIUM`

| Estimator | h=1 | h=5 | h=10 | Verdict |
| --- | ---: | ---: | ---: | --- |
| Fixed anchor `10000` | 3.86 | 3.86 | 3.86 | Useful sanity anchor, too coarse for execution |
| Simple mid | 1.25 | 1.41 | 1.56 | Acceptable baseline |
| Microprice | 1.24 | 1.41 | 1.55 | Similar level estimate, more useful as lean |
| Wall mid | 1.14 | 1.26 | 1.39 | Strong level estimator |
| Filtered MM mid `>=10` | 1.04 | 1.21 | 1.36 | Best tested level estimator |

Interpretation:
- `ASH` does behave like an anchored market, but the actionable fair is not a naked `10000`.
- The best short-horizon execution fair comes from the visible book, especially the `>=10` filtered market-maker mid.
- `microprice` is not the best level estimate, but it is directionally useful.

### `INTARIAN_PEPPER_ROOT`

| Estimator | h=1 | h=5 | h=10 | Verdict |
| --- | ---: | ---: | ---: | --- |
| Fixed anchor `10000` | 1501.03 | 1501.25 | 1501.52 | Falsified immediately |
| Linear intraday trend fit | 1.09 | 1.20 | 1.47 | Drift matters materially |
| Simple mid | 1.08 | 1.30 | 1.58 | Too naive |
| Microprice | 1.01 | 1.23 | 1.53 | Better as skew than as base fair |
| Wall mid | 0.96 | 1.16 | 1.45 | Best tested base fair |
| Filtered MM mid `>=10` | 0.96 | 1.17 | 1.46 | Near-tie with wall mid, slightly worse overall |

Interpretation:
- `PEPPER` must be treated as rolling fair value, not fixed-fair-value market making.
- The right base fair is time-aware and book-aware.
- `wall_mid` edges out `mm10` on this product, while `microprice` still helps as a directional overlay.

## Local Findings by Product

### `ASH_COATED_OSMIUM`

#### What the raw data says

- Intraday mid is tightly centered around `10000`:
  - day `-2`: mean `9998.16`, std `4.73`
  - day `-1`: mean `10000.83`, std `3.83`
  - day `0`: mean `10001.62`, std `5.22`
- Drift is negligible: roughly `0` per step across all three days.
- Spread is wide and stable:
  - mean `16.18`
  - dominant regime `16`
  - secondary regimes `18` and `19`

#### Spread regimes

- Spread-state persistence exists mechanically because `16` dominates the book, but it is not a strong alpha source.
- Narrow-vs-wide spread response is weak:
  - narrow spreads: average `+0.14` over 5 ticks
  - wide spreads: average `-0.01` over 5 ticks
- Conclusion: spread is mainly an execution-cost input, not a primary predictor.

#### Imbalance and short-horizon return behavior

- Top-level imbalance is not persistent:
  - lag-1 imbalance autocorrelation is near `0`
  - strong-sign imbalance keeps the same sign only about `16%` of the time on the next row
- But current imbalance still predicts short-horizon direction:
  - negative imbalance bucket: about `-1.9` over 5 ticks
  - positive imbalance bucket: about `+2.0` over 5 ticks
- `microprice` and `mm10` lean directionally the right way:
  - `microprice > mid`: average `+1.91` over 5 ticks
  - `microprice < mid`: average `-1.82` over 5 ticks
  - `mm10 > mid`: average `+4.05` over 5 ticks
  - `mm10 < mid`: average `-3.50` over 5 ticks

Interpretation:
- There is usable book-driven lean.
- The effect size is still small relative to the `16`-tick spread, so this is a quote-skew / selective-taking signal, not a license for constant aggressive crossing.

#### Quote-wall behavior

- Back-of-book walls show a small bounce-away effect, not a large follow-through effect:
  - bid-side wall case: about `-0.31` residual move over 5 ticks
  - ask-side wall case: about `+0.33` residual move over 5 ticks
- This is too small to rank as a primary edge.

#### Spike behavior

- Short-horizon jumps do revert often:
  - spike threshold around `3.8` to `3.9`
  - 689 to 761 spike cases per day under that rule
  - reversion rate over 5 ticks: about `71%` to `74%`
  - average 5-tick reversion: about `2.45` to `2.52`

Interpretation:
- Spike fading is real, but still smaller than the full spread.
- Best use: temporary contra-skew or inventory relief, not a standalone high-turnover reversal engine.

#### Trade tape

- Anonymous trades do not carry strong follow-through in `ASH`.
- Prints at the bid or ask are close to flat on a 5-tick horizon.

Conclusion:
- `ASH` is a stable market-making product first.
- Best fair base: `mm10`, with `wall_mid` as a simpler near-equivalent fallback.
- Best overlay: mild book-based lean plus optional spike-fade skew.

### `INTARIAN_PEPPER_ROOT`

#### What the raw data says

- Each local day rises by about `+1000` from open to close:
  - day `-2`: `9998.5 -> 11001.5`
  - day `-1`: `10998.5 -> 11998.0`
  - day `0`: `11998.5 -> 13000.0`
- Fitted slope is extremely consistent:
  - about `+0.108` mid units per step on each day
- After removing that linear drift, residual volatility is small:
  - residual std about `1.36` to `1.62`

Interpretation:
- The dominant feature is deterministic / session-like drift.
- Residual microstructure exists, but it sits on top of that drift rather than replacing it.

#### Spread regimes

- Spread is narrower than `ASH` and mostly lives in `12` to `14` on days `-2` and `-1`, then `13` to `17` on day `0`.
- Spread state has only weak predictive value:
  - narrow-spread average 5-tick move: `+0.56`
  - wide-spread average 5-tick move: `+0.54`
- That is basically just the background drift.

Conclusion:
- The prompt hint that spread may encode “intention” is only weakly supported here.
- Spread looks more like an execution-state variable than a standalone alpha.

#### Imbalance and short-horizon return behavior

- Raw imbalance has little persistence, same as `ASH`.
- Once drift is removed, imbalance still matters:
  - negative imbalance residual move: about `-1.64` to `-2.02` over 5 ticks
  - positive imbalance residual move: about `+1.70` to `+1.95` over 5 ticks
- `microprice` is the best directional overlay:
  - `microprice > mid`: average `+2.37` over 5 ticks
  - `microprice < mid`: average `-1.25` over 5 ticks

Interpretation:
- `PEPPER` has both drift and subtle repeated one-sided pressure.
- A rolling fair should lean upward by default, then further skew on positive book pressure.

#### Trade tape

- The tape is informative even though buyer/seller IDs are anonymized:
  - trades at or above the ask are followed by about `+2.03`, `+2.37`, `+2.69` over 5 ticks on the three days
  - trades at or below the bid are followed by about `-0.42`, `-0.98`, `-0.79`

Interpretation:
- Repeated directional pressure is real.
- This supports a light continuation overlay on top of the session drift.

#### Quote-wall behavior

- Back-of-book wall effects are again small:
  - bid-side wall residual move: about `-0.24` to `-0.33` over 5 ticks
  - ask-side wall residual move: about `+0.29` to `+0.32`
- This is too weak for a standalone wall strategy.

#### Spike behavior

- Raw spikes often revert:
  - spike threshold around `3.16` to `3.75`
  - reversion rate over 5 ticks about `72%` to `74%`
- But this is not the main story.
- Once the deterministic drift is accounted for, spike-fade is secondary and should not override the rolling-fair-value logic.

Conclusion:
- `PEPPER` is a drift-tracking market-making product with secondary microstructure continuation.
- Best fair base: time-aware rolling fair with `wall_mid` refinement.
- Best overlay: `microprice` / tape-confirmed upward pressure, used carefully to skew rather than blindly chase.

## Ranked Candidate Edges

| Rank | Edge | Support class | Why it ranks here | Monetization path | Main failure mode |
| --- | --- | --- | --- | --- | --- |
| 1 | `INTARIAN_PEPPER_ROOT` session drift tracking with rolling fair and upward skew | Supported by local data | The `+1000/day` drift is the clearest, largest, most repeatable pattern in the sample | Quote around a rising fair, buy stale asks, avoid donating with stale sells, inventory-aware skew | Drift disappears, reverses, or becomes non-linear live |
| 2 | `ASH_COATED_OSMIUM` anchored market making around `mm10` / `wall_mid` | Supported by local data | Stable center around `10000`, stable wide spread, best clean spread-capture setup | Two-sided passive quoting plus selective stale-quote takes | Hidden fair drifts more in live than in sample |
| 3 | `ASH` book-lead overlay from `mm10`, `microprice`, and imbalance | Supported by local data | Directional effect exists, but it is smaller than the spread | Use as quote skew and selective taking filter, not as pure directional strategy | Overtrading small signals gives up spread edge |
| 4 | `PEPPER` continuation overlay from `microprice` and trade-at-ask / trade-at-bid pressure | Supported by local data | Trade tape and book both show repeated one-sided pressure beyond baseline drift | Lean quotes upward after buy pressure, be slower to offer size into strength | Inventory builds too fast in an already drifting product |
| 5 | `ASH` short-horizon spike fade | Supported by local data | Reversion exists, but payoff is modest relative to spread | Temporary contra-skew, inventory relief, occasional selective fade | Fading too aggressively in a genuine move |
| 6 | Calm quote placement, context-aware sizing, inventory-aware skew | Supported only by public analogy plus prompt hints | Strong execution pattern, but not directly inferable from the sample alone | Better fill quality and lower adverse selection | Hidden if backtester fills are too optimistic |

## Explicitly Rejected or Downgraded Ideas

- Reject as primary edge: spread-regime alpha on either product.
  - The spread is observable and worth logging, but predictive content is weak.
- Reject: `INTARIAN_PEPPER_ROOT` fixed-anchor market making.
  - The local sample falsifies this immediately.
- Reject as primary edge: standalone quote-wall direction trading.
  - Effects are too small and sign is more “bounce away from the wall” than “follow the wall.”
- Downgrade heavily: `PEPPER` pure spike-reversion strategy.
  - Drift is the dominant state variable; spike fading is secondary.
- Downgrade: `ASH` periodicity / bot-cycle timing models.
  - I do not see enough direct raw-data support to elevate periodicity above book-state signals.
- Downgrade: aggressive directional crossing from small book signals on either product.
  - Signal magnitudes are smaller than the quoted spread; this belongs in skew logic first.

## Comparison Against Prompt Hints

### What the hints got right

- `INTARIAN_PEPPER_ROOT` really does behave like a slow market with subtle leaning.
- There is repeated small directional pressure beyond a naive “stable commodity” model.
- Calm execution is likely important because the usable signal sizes are modest relative to spread.

### What the hints overstate or leave unproven

- “Spread behaving like intention” is not strongly confirmed by the raw local data.
- The strongest `PEPPER` effect is not just subtle leaning; it is a nearly mechanical session drift with smaller microstructure overlays.
- `ASH` looks less like hidden long-cycle trend discovery and more like wide-spread stationary market making with short-horizon book patterns.

## Comparison Against `ai_strategy_context.zip`

### Agreement

- `ASH` is stable / stationary.
- `PEPPER` is drifting and should use rolling fair value.
- `wall_mid` is a strong estimator on both products.
- `ASH` has real mean-reverting behavior after jumps.

### Adjustments I would make

- For `ASH`, the filtered market-maker mid only wins cleanly under the exact visible-level `>=10` definition. A stricter “large quote” threshold loses quality.
- For `PEPPER`, `wall_mid` remains the cleanest base estimator. Filtered MM mid is basically a tie, not an upgrade.
- I would not rank periodicities as tradeable evidence from the current raw sample.
- I would not promote `PEPPER` spike-reversion or spread-state ideas above drift-tracking and directional-pressure overlays.

## Bottom Line

- `ASH_COATED_OSMIUM` should be treated as a stable wide-spread market-making product with `mm10` or `wall_mid` fair, plus small directional skew from the book.
- `INTARIAN_PEPPER_ROOT` should be treated as a rolling-fair-value drift product first, with `wall_mid` refinement and a secondary `microprice` / tape-pressure continuation overlay.
- The strongest rejected idea is “spread state itself is alpha.”
- The strongest caution is that `PEPPER` inventory can build quickly if drift and buy pressure are monetized too aggressively without skew discipline.
