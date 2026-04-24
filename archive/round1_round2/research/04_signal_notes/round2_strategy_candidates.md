# Round 2 Strategy Candidates

Date: 2026-04-19

Scope: compact implementation-ready handoff from the Round 2 alpha search.

## Ranking Summary

| Slot | Strategy family | Why it ranks here |
|---|---|---|
| Best conservative | Pepper dynamic-fair residual taker with soft cap | strongest structural edge with the smallest idea count |
| Best balanced | Pepper dynamic fair + Ash anchored maker | uses the strongest product-specific shell for each asset without forcing shared logic |
| Best aggressive | Pepper dynamic fair + quote-EV gate + Ash spike/event overlay | highest plausible upside, also highest local-overfit risk |
| Best exploit of Pepper | residual mean reversion around `mm_mid` with imbalance skew | strongest Round 2 signal stack and best monetization evidence |
| Best exploit of Osmium | anchored `wall_mid` market making with spike fade | strongest Ash edge while respecting its execution limits |
| Hybrid two-product view | Pepper-first risk budget, Ash as low-complexity anchor sleeve | best use of implementation time and complexity budget |

## Conservative

### `PEPPER_DYNAMIC_FAIR_BASELINE`

Why it should work:

- Pepper is the strongest Round 2 product.
- `z20`, `wall_delta`, and `mm_delta` are strong and stable.
- Buy and sell take markouts are positive.

Signals used:

- dynamic fair residual (`mid - mm_mid` or smoothed blend)
- `z20`
- optional light `imb_l1` side bias

Fair proxy:

- primary: `mm_mid`
- fallback check: `wall_mid`

Likely robustness:

- high among current candidates because it uses the strongest structural family
  and avoids extra execution modelling.

Main failure mode:

- inventory drift from repeatedly leaning into residuals without a soft cap.

Smallest implementation:

- maintain a smoothed `mm_mid` fair
- cross the spread when deviation exceeds about `3.25`
- clear near fair
- stop adding risk beyond about `50%` to `60%` of the hard limit

## Balanced

### `PEPPER_DYNAMIC_FAIR_PLUS_ASH_ANCHOR`

Why it should work:

- keeps Pepper as the alpha engine
- keeps Ash simple and stable
- avoids spending complexity budget on speculative Ash controllers

Signals used:

- Pepper: `z20`, fair deviation, `imb_l1`
- Ash: `wall_mid` deviation, spike flag, light imbalance side bias

Fair proxy:

- Pepper: `mm_mid`
- Ash: `wall_mid`

Likely robustness:

- high relative to more ambitious hybrids because each product uses its own
  natural structure.

Main failure mode:

- implementation drift where Ash logic becomes too complex and starts fighting
  the anchored shell.

Smallest implementation:

- one per-product router
- Pepper uses dynamic-fair take/clear
- Ash uses anchored make/clear plus spike fade
- shared inventory serialization only, no shared fair logic

## Aggressive

### `PEPPER_GATE_PLUS_ASH_EVENT`

Why it should work:

- attacks the likely remaining Pepper bottleneck: quote selection / bad-fill
  suppression
- preserves the stable Ash event edge without overengineering its base shell

Signals used:

- Pepper base: dynamic fair residuals, `z20`, `imb_l1`
- Pepper gate: spread state, side, residual size, position, recent fill context
- Ash: fair deviation and spike regime

Fair proxy:

- Pepper: smoothed `mm_mid`
- Ash: `wall_mid`

Likely robustness:

- medium. Highest upside, but the extra gate is the most likely place to encode
  local-fill artefacts.

Main failure mode:

- the quote gate learns the local replay instead of transfer edge and simply
  throttles too much good activity.

Smallest implementation:

- keep the conservative Pepper baseline intact
- add only a bucketed quote/no-quote gate
- do not mix that with a second new Pepper fair model in the same iteration

## Best Exploit Of Pepper

### `PEPPER_RESIDUAL_REVERSION_WITH_SKEW`

Why it should work:

- strongest Round 2 structural edge
- cleanest product-level improvement from Round 1 to Round 2
- execution evidence supports taking and clearing

Signals used:

- `z20`
- `mid - mm_mid`
- `wall_delta` / `mm_delta`
- `imb_l1` as skew

Fair proxy:

- `mm_mid`

Likely robustness:

- high, provided fair smoothing is not overfit.

Main failure mode:

- a too-reactive fair estimate turns the strategy into chasing the move instead
  of fading the deviation.

Smallest implementation:

- smoothed `mm_mid`
- thresholded takes at about `3.25`
- clearer around fair or inside one tick
- one-sided quote skew when `imb_l1` is extreme

## Best Exploit Of Osmium

### `ASH_ANCHORED_MAKER_WITH_SPIKE_FADE`

Why it should work:

- Ash carryover is unusually stable across rounds
- anchored fair and spike fade both survive
- aggressive taker-first logic remains unsupported

Signals used:

- `mid - wall_mid`
- `z20`
- spike flag from short-term return vs rolling vol
- `imb_l1` only as quote-side bias

Fair proxy:

- `wall_mid`

Likely robustness:

- medium-high if kept simple.

Main failure mode:

- overexpanding the passive layer or adding too many directional overlays.

Smallest implementation:

- quote around `wall_mid`
- cross only on clear fair-value dislocations
- fade spikes in small size
- flatten earlier once inventory leaves the centre

## Hybrid Two-Product Portfolio View

### `PEPPER_FIRST_ASH_SECOND`

Portfolio view:

- Pepper should receive the main complexity and inventory budget.
- Ash should remain a lower-complexity sleeve that stabilizes total strategy
  behavior rather than dominating expected edge.

Why:

- Pepper has the strongest monetizable Round 2 structure.
- Ash is stable but execution-limited; extra sophistication there is more
  likely to overfit than to unlock a large new edge.

Failure mode:

- giving Ash and Pepper symmetric complexity and ending up with two mediocre
  sleeves instead of one strong Pepper sleeve plus one disciplined Ash sleeve.

Smallest implementation:

- build Pepper first
- keep Ash as anchored make/clear/event-fade
- share only serialization, position accounting, and logging infrastructure
