# Round 1 Signal Ranking

Date: 2026-04-14

Scope: `alpha_miner` adversarial mechanism analysis of the local Round 1 bundle for `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.

Primary sources:
- Official files under `Prosperity Context/`
- Local Round 1 datasets under `prosperity_rust_backtester/datasets/round1/`
- Existing Round 1 research notes under `prosperity-research/`

Public-repo material was not used as authority for any current Round 1 mechanism claim.

## Source Status

### Confirmed by official docs

- Round 1 products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Both position limits are `80`.
- Round 1 uses the normal `Trader.run(self, state)` continuous-book interface.
- The Exchange Auction exists, but it is a separate side task.
- Narrative prompt cards and screenshots are soft clues, not formal rules.

### Supported by local data

- `ASH_COATED_OSMIUM` is anchored near `10000` and behaves like a replenishing wide-spread maker market.
- `INTARIAN_PEPPER_ROOT` follows an extremely repeatable rising session path in the local three-day bundle.
- Pepper one-sided books are short refresh artifacts, not durable states.
- Pepper's time-of-session path explains more of the local sample than book-only fair proxies do.
- Pepper imbalance still matters, but mainly as a local overlay on top of the session ramp.

### Still unproven

- Whether the Pepper session ramp persists live outside the local three-day bundle.
- Whether the Pepper ramp is literally scripted by time, or instead produced by lagged bots reacting to a hidden fair that itself follows a stable template.
- Whether Ash has a deeper periodic generator beyond anchored replenishment and microstructure fade.

## Re-Tested Prior Conclusions

The prior local story still holds after adversarial slicing, but the causal interpretation is now sharper.

What still looks right:
- Ash is not a time-template market.
- Pepper is not well described as a fixed-anchor market.
- One-sided Pepper books should not be promoted to first-class state variables.

What needed tightening:
- Pepper does not merely "trend upward."
- The local evidence says Pepper follows a near-deterministic session-shaped fair path, with the visible book mostly revealing that path plus small local deviations.
- The strongest competition-specific edge is therefore not generic trend following. It is exploiting what looks locally like a telegraphed session fair.

## Adversarial Empirical Findings

## 1. Price Process Structure

### `ASH_COATED_OSMIUM`

- Effective two-sided mid by day:
  - day `-2`: `10000.0 -> 9993.5`
  - day `-1`: `9992.0 -> 10002.0`
  - day `0`: `10003.0 -> 10007.0`
- Daily std of effective mid: about `3.8` to `5.2`.
- Cross-day normalized path correlation is weak or slightly negative:
  - `-2/-1`: `-0.0969`
  - `-2/0`: `-0.1391`
  - `-1/0`: `-0.0878`
- Leave-one-day-out current-fair MAE:
  - `mm10_mid`: `0.288`
  - `microprice`: `0.981`
  - `wall_mid`: `0.979`
  - `ema_wall`: `1.244`
  - time template: `7.862`
- Ten-step-ahead MAE:
  - `mm10_mid`: `1.336`
  - `microprice`: `1.528`
  - `wall_mid`: `1.666`
  - time template: `7.868`

Interpretation:
- Ash is anchored and locally book-driven.
- Time-of-session does not explain Ash.
- The right fair story is still anchored maker + small book-based lean.

### `INTARIAN_PEPPER_ROOT`

- Effective two-sided mid by day:
  - day `-2`: `9998.5 -> 11001.5`
  - day `-1`: `10998.5 -> 11998.0`
  - day `0`: `11998.5 -> 13000.0`
- Daily std of effective mid: about `288.7` every day.
- Cross-day normalized path correlation is effectively `1.0`:
  - `-2/-1`: `0.999983`
  - `-2/0`: `0.999982`
  - `-1/0`: `0.999980`
- Decile normalized path points are almost identical across days:
  - day `-2`: `[0.0, 101.0, 202.5, 302.5, 400.5, 500.0, 601.5, 700.0, 801.5, 900.0, 1003.0]`
  - day `-1`: `[0.0, 103.0, 201.5, 303.0, 403.0, 501.5, 601.5, 700.0, 806.0, 901.0, 999.5]`
  - day `0`: `[0.0, 101.0, 199.5, 301.5, 401.5, 501.5, 603.0, 703.0, 803.0, 901.5, 1001.5]`
- Third-session slopes are almost constant:
  - day `-2`: `[0.1005, 0.1004, 0.1001]`
  - day `-1`: `[0.1004, 0.1001, 0.0995]`
  - day `0`: `[0.1005, 0.1001, 0.0999]`
- Leave-one-day-out current-fair MAE:
  - `mm10_mid`: `0.3845`
  - `microprice`: `0.7050`
  - time template: `1.0153`
  - `wall_mid`: `1.0474`
  - `ema_wall`: `1.6506`
- Ten-step-ahead MAE:
  - time template: `1.0156`
  - `mm10_mid`: `1.4260`
  - `microprice`: `1.4749`
  - `wall_mid`: `2.2195`
  - `ema_wall`: `2.6210`

Interpretation:
- Pepper's local fair path is far more clock-like than book-like.
- The book still helps for local alignment and short-horizon tilt, but the dominant structure is a session template.

## 2. Return Structure And Regime Persistence

### Both products

- One-step return autocorrelation is strongly negative:
  - Ash: `-0.4578`
  - Pepper: `-0.4506`
- Longer-lag return autocorrelation is near zero.

Interpretation:
- Both books exhibit short-horizon quote bounce / replenishment effects.
- There is no evidence that simple return-momentum logic is the primary engine.

### Pepper drift stability under slicing

Pepper ten-step effective-mid return stays near `+1.0` tick under hard slicing:

- early / mid / late session:
  - `1.0005`, `0.9995`, `1.0004`
- after excluding top `5%` of ten-step moves:
  - full sample: `1.0001`
  - trimmed: `0.8938`
- in ordinary two-sided states:
  - `0.9949`
- after recent trade activity:
  - no recent trade: `0.9947`
  - recent trade: `1.0499`
- after just-refreshed books:
  - just refreshed: `0.9399`
  - not refresh: `1.0046`

Interpretation:
- The Pepper ramp is not a few bursts.
- It persists by day, by segment, by ordinary book state, and after trimming extremes.

## 3. Spread And Book Behavior

### `ASH_COATED_OSMIUM`

- State counts per day are about:
  - two-sided: `9187` to `9232`
  - one-sided bid/ask combined: about `750` to `795`
  - empty: about `14` to `18`
- Non-two-sided streak median is `1`, max `2` to `4`.
- Dominant spreads:
  - `16`, `18`, `19`
- Spread state has only small predictive value once the anchored fair is accounted for.

### `INTARIAN_PEPPER_ROOT`

- State counts per day are about:
  - two-sided: `9216` to `9253`
  - one-sided bid/ask combined: about `726` to `794`
  - empty: about `16` to `21`
- Non-two-sided streak median is `1`, max `3`.
- Ordinary spreads from `11` to `18` all still carry about the same ten-step drift, roughly `+0.97` to `+1.04`.

Interpretation:
- One-sided Pepper books are overwhelmingly refresh artifacts.
- Spread regime is not the main causal state for Pepper. The session fair is.

## 4. Imbalance Persistence And Book Alpha

### `ASH_COATED_OSMIUM`

- Top-of-book imbalance correlates with future effective-mid returns:
  - `h=1`: `0.5665`
  - `h=5`: `0.5535`
  - `h=10`: `0.5191`
  - `h=20`: `0.4779`
- Ten-step future return by imbalance bucket:
  - `pos_hi`: `+3.8935`
  - `pos`: `+1.6681`
  - `flat`: `-0.0116`
  - `neg`: `-1.6137`
  - `neg_hi`: `-3.2974`

Interpretation:
- Ash imbalance is real alpha and consistent with maker skew / selective taking.

### `INTARIAN_PEPPER_ROOT`

- Top-of-book imbalance correlates with future effective-mid returns:
  - `h=1`: `0.5436`
  - `h=5`: `0.5612`
  - `h=10`: `0.5700`
  - `h=20`: `0.5635`
- Ten-step future return by imbalance bucket:
  - `pos_hi`: `+6.8729`
  - `pos`: `+2.7411`
  - `flat`: `+0.9728`
  - `neg`: `-0.7877`
  - `neg_hi`: `-4.4677`

Interpretation:
- Pepper imbalance matters.
- But the key adversarial point is this: even flat imbalance still gives about `+1.0` tick over ten steps.
- Imbalance modulates a rising fair. It does not generate the whole drift.

## 5. Time Template Versus Book Revelation

This is the strongest competition-specific result in the local bundle.

### Pepper time-template evidence

- Pepper leave-one-day-out time-template ten-step MAE is `1.0156`, better than any tested book-only proxy.
- Pepper residual around the leave-one-day-out template has std about `1.52`.
- Pepper wall-minus-template residual has std about `1.41`.
- Relative to the full intraday Pepper scale, those residuals are tiny.

### Does the book add information beyond the template?

Yes, but mainly as a local reveal / overshoot signal.

Correlation of `(wall_mid - template_now)` with excess future return over the template path:
- `h=1`: `-0.5281`
- `h=5`: `-0.5609`
- `h=10`: `-0.5549`
- `h=20`: `-0.5505`

Interpretation:
- If wall-mid is above the template, future excess return tends to be smaller or mean-reverting.
- If wall-mid is below the template, future excess return tends to be larger.
- That is exactly what a lagged noisy book reveal should look like around a dominant latent fair path.

Conclusion:
- Pepper's book is more consistent with revealing and locally overshooting a template fair than with causing the main drift.

## 6. Trades, Quote Changes, And Refresh Artifacts

### `ASH_COATED_OSMIUM`

- Trade relation counts:
  - sell-hit: `618`
  - buy-lift: `647`
- Average next effective-mid move:
  - after any trade row: `+0.0519`
  - after no-trade row: `-0.0020`
- Trade-signed impact is small:
  - buy-lifts, `h=10`: `+0.1731`
  - sell-hits, `h=10`: `-0.0712`
- `P(next book change | trade)` is not elevated versus no trade:
  - trade: `0.6989`
  - no trade: `0.7235`

Interpretation:
- Ash is not dominated by trade-triggered quote chasing.
- Replenishing liquidity remains the better story.

### `INTARIAN_PEPPER_ROOT`

- Trade relation counts:
  - sell-hit: `518`
  - buy-lift: `492`
  - inside: `1`
- Average next effective-mid move:
  - after any trade row: `+0.3049`
  - after no-trade row: `+0.0929`
- Trade-signed impact:
  - buy-lifts: `+1.6423` at `h=1`, `+2.6443` at `h=10`
  - sell-hits: `-0.9411` at `h=1`, `-0.1535` at `h=10`
- `P(next book change | trade)` is clearly elevated:
  - trade: `0.7527`
  - no trade: `0.6774`
- `P(next trade | prior book change)` only rises slightly:
  - change: `0.0344`
  - no change: `0.0318`

Interpretation:
- Pepper trades look more like triggers for later quote updates than quote updates look like triggers for later trades.
- That supports lagged quote bots or stale-update bots, not purely book-led price discovery.

## 7. Clocked Quote Updates And Template Bots

### What is true

- Pepper quote shifts use a small discrete menu:
  - best-bid top shifts: `+3`, `-3`, `+1`, `-2`, `+4`, `+2`, `+9`, `-9`
  - best-ask top shifts: `+3`, `-3`, `+1`, `-2`, `+4`, `+2`, `-4`, `-10`
- Pepper change intervals favor short gaps:
  - `1`, `2`, `3`, `4`, `5`, `6`, `10`

### What is not true

- Cross-day quote-increment sequence correlation is near zero:
  - Pepper best-bid increment sequence correlation across day pairs is roughly `-0.0147` to `0.0246`
  - Pepper best-ask increment sequence correlation across day pairs is roughly `0.0048` to `0.0132`
- Change counts by `timestamp mod 10` are not tightly concentrated.

Interpretation:
- The local data do not support a naive "same quote update at the same clock tick every day" story.
- The better story is a stable latent fair path rendered through noisy discrete update templates.

## 8. Hidden Periodic Structure

### `ASH_COATED_OSMIUM`

- After removing the anchor, Ash levels are persistent, but there is no clean periodic signature.
- The high short-lag level autocorrelation looks like anchored mean reversion and slow book evolution, not a detectable session clock.

### `INTARIAN_PEPPER_ROOT`

- After removing the leave-one-day-out time template, residual lag correlations are small.
- No additional strong periodic residual structure emerges.

Interpretation:
- Pepper's main periodicity is the session fair itself.
- Ash does not show a second, strong, exploitable session clock in the local bundle.

## Ranked Mechanism Hypotheses

## `INTARIAN_PEPPER_ROOT`

### 1. Smooth session-template latent fair with lagged discrete quote bots

Mechanism:
- A latent fair rises at an almost fixed session slope.
- Visible quotes are a noisy, discrete, delayed rendering of that fair.
- Trades sometimes trigger book refreshes, but they do not create the whole move.

Explains well:
- near-perfect normalized path repeatability
- constant third-session slopes
- time-template forecast dominance at ten-step horizon
- trade leading later quote changes
- discrete but not cross-day-synchronized quote shifts
- wall-vs-template mean reversion

Fails to explain:
- why imbalance is still strong without adding the "lagged reveal" piece

Favored strategy families:
- time-template fair ownership
- carry / acquire-and-defend long inventory
- template fair plus local book overshoot correction

Punished if wrong:
- fully ramp-committed long carry
- fast max-long acquisition

Verdict:
- strongest local mechanism hypothesis

### 2. Synthetic near-deterministic fair path plus noisy book renderer

Mechanism:
- The simulator may effectively specify a fair path first, then generate book states around it.
- The book is more presentation layer than driver.

Explains well:
- tiny template residuals
- cross-day path stability
- weak cross-day correlation of exact quote increments

Fails to explain:
- trade-triggered quote refresh patterns unless paired with update bots

Favored strategy families:
- competition-specific time-template exploitation
- simple fair-carry strategies with only modest book conditioning

Punished if wrong:
- strategies that ignore the book completely

Verdict:
- very plausible locally, but slightly less complete than hypothesis 1

### 3. Rising fair with imbalance-modulated local drift

Mechanism:
- The dominant fair rises exogenously, while current imbalance changes local timing and overshoot.

Explains well:
- strong imbalance correlations
- flat-imbalance state still having positive drift
- large positive returns in `pos_hi` and negative returns in `neg_hi`

Fails to explain:
- near-perfect cross-day path without adding the session template

Favored strategy families:
- template fair plus state-conditioned aggression
- adaptive carry with reserve capacity

Punished if wrong:
- pure imbalance followers

Verdict:
- useful execution overlay, not the root story

### 4. Book-driven hidden-state trend regime

Mechanism:
- The book itself carries persistent directional states and the local sample happened to over-sample upward states.

Explains well:
- strong imbalance alpha

Fails to explain:
- flat imbalance still drifting up
- one-sided states being brief
- the near-identical daily path

Favored strategy families:
- hidden-state book followers

Punished if wrong:
- one-sided-book chasing
- spread-state-first logic

Verdict:
- weaker than the time-template explanation

### 5. Clocked quote-template bot with same updates every day

Mechanism:
- Bots update on a fixed clock schedule with repeated exact shift patterns.

Explains well:
- discrete quote increments

Fails to explain:
- near-zero cross-day quote increment alignment
- lack of strong timestamp-modulo concentration

Favored strategy families:
- exact clock-arbitrage on quote moves

Punished if wrong:
- rigid event-time entry timing

Verdict:
- rejected as the main story

## `ASH_COATED_OSMIUM`

### 1. Anchored replenishing maker market with small book-led deviations

Mechanism:
- A stable fair near `10000`.
- Wide quoted spread.
- Replenishing liquidity with modest imbalance information.

Explains well:
- strong `mm10_mid` fit
- anchored daily range
- imbalance-to-return correlation
- weak time-template fit

Fails to explain:
- any larger hidden periodic component

Favored strategy families:
- anchored market making
- book-skewed quoting
- selective stale-quote taking

Punished if wrong:
- directional momentum engines

Verdict:
- strongest Ash mechanism

### 2. Anchored fair with short spike-fade microstructure

Mechanism:
- Short deviations around the anchor mean-revert quickly.

Explains well:
- negative one-step autocorrelation
- small signed trade impact
- microprice usefulness as an overlay

Fails to explain:
- the whole Ash edge by itself

Favored strategy families:
- anchored MM plus small fade overlays

Punished if wrong:
- over-aggressive contrarian taking

Verdict:
- good overlay, not full architecture

### 3. Hidden periodic session clock

Mechanism:
- Ash fair follows a repeated session pattern.

Explains well:
- little

Fails to explain:
- weak or negative cross-day path correlation
- poor template MAE
- near-zero cross-day quote increment alignment

Favored strategy families:
- time-template Ash logic

Punished if wrong:
- any clock-driven Ash positioning

Verdict:
- rejected

## Strategy Families Favored Or Punished

### Favored by the current mechanism map

1. Pepper time-template fair ownership with inventory tolerance.
2. Pepper template fair plus local book overshoot correction.
3. Ash anchored market making with `mm10_mid` / `wall_mid` and imbalance skew.
4. Competition-specific hybrid: time-shaped Pepper carry plus conservative Ash spread capture.

### Punished by the current mechanism map

1. Fixed-anchor Pepper market making.
2. One-sided-book Pepper chasing as a primary alpha.
3. Exact clock-tick quote-arbitrage without a latent-fair story.
4. Time-template Ash logic.
5. Purely reactive Pepper book-only strategies that refuse to encode session shape.

## Competition-Specific Exploit Takeaway

If this Round 1 environment is synthetic rather than real-market-like, the locally rational exploit is:
- treat Pepper as a telegraphed session fair first,
- use the visible book as a noisy reveal and overshoot control layer,
- and tolerate inventory concentration more than a real-market trader normally would.

That is not an official fact.
It is the strongest local mechanism inference currently supported by the bundle.

## Bottom Line

- Ash is best understood as an anchored replenishing-maker market with real but modest book alpha.
- Pepper is best understood as a competition-specific session-template fair rendered through lagged discrete quote updates.
- The strongest local Round 1 edge is therefore a hybrid:
  - real-market-like logic for Ash,
  - competition-specific template exploitation for Pepper.

## Current Ship Re-Read

### What `round1_overhaul_v1.py` gets right

- It already abandons fixed-anchor Pepper market making.
- It correctly leans into early Pepper ownership instead of waiting for repeated confirmation that arrives too late.
- It keeps Ash in the right family: anchored fair, maker-first, selective taking, modest book overlays.

### What `round1_overhaul_v1.py` still over-assumes

- It treats Pepper mainly as a reactive drift state inferred from the current book and opening observations.
- It does not encode the stronger local evidence that Pepper's fair path itself is session-shaped and near-deterministic in the local bundle.
- It therefore captures the right carry posture, but not the cleanest generator story behind that posture.

## Candidate-Family Ranking

| Family | Market hypothesis | Generator hypothesis | Why it might beat `round1_overhaul_v1.py` | Failure mode | Verdict |
| --- | --- | --- | --- | --- | --- |
| Improved Ash maker + improved Pepper ramp ownership | Ash anchored maker, Pepper rising fair | Pepper fair rises on a stable session template | Own the same Pepper edge earlier and with cleaner fair anchoring | Still fragile if the template weakens live | Strong |
| Time-template Pepper strategy | Pepper is primarily clock-shaped | Synthetic or exogenous session fair dominates the visible book | Converts the local mechanism map directly into fair estimation | Overfits if the ramp is only a three-day coincidence | Strong |
| Explicit generator-aware strategy | Book is a lagged renderer of a hidden session fair | Stable latent fair plus noisy quote updates | Uses time template first and book residual second | Too aggressive if book-only states matter more live | Strong |
| Adaptive carry with reserve capacity | Same Pepper fair, but uncertainty deserves spare capacity | Template exists, but only some sessions should be fully owned | Better fallback if the live ramp weakens | Gives away too much bundle PnL if the template is real | Medium |
| Structural exploit candidate | Refresh / template artifacts are themselves tradable | Small family of quote-template bots | Could beat carry by timing discrete refreshes | Evidence too weak for exact clock exploitation | Rejected |
| Full overhaul candidate | Product-specific logic with no architecture constraint | Ash anchored maker, Pepper template fair with local overshoot control | Best chance to align code with the mechanism map | Complexity without evidence | Chosen family |
| Robust fallback candidate | Lower Pepper concentration, more reactive logic | Generator remains partly unidentified | Less single-story dependence | Leaves too much edge unowned if the bundle story holds | Reserve only |

## Implemented Contenders

### `round1_overhaul_v3.py`

- Ash logic stays in the anchored-maker family from `v1`.
- Pepper is redesigned around an explicit session-template fair using a locally derived offset curve.
- The book is used as a secondary reveal / overshoot control layer, not as the primary source of drift.
- Inventory policy is intentionally competition-specific: acquire and defend long Pepper earlier when price sits below the template fair.

Why it is strategically distinct from `round1_overhaul_v1.py`:
- `v1` mostly infers a rising Pepper state from current book conditions.
- `v3` encodes the stronger local generator hypothesis directly: session-template fair first, local book second.

### `round1_overhaul_v4.py`

- `v4` is the slower-build counterfactual.
- It preserves the same template story but holds more reserve capacity and delays max-long acquisition.
- Its main value is diagnostic:
  - if it had matched or beaten `v3`, the case for immediate template ownership would have weakened.
  - it did not.

## Candidate Outcome Ranking

1. `round1_overhaul_v3.py`
   Why: best alignment with the current mechanism map and best stressed local validation.
2. `round1_overhaul_v1.py`
   Why: simpler and already strong, but it under-specifies the session-template story.
3. `round1_overhaul_v4.py`
   Why: useful falsification test, but dominated by `v3`.
4. `round1_candidate_v2.py`
   Why: lower-concentration fallback when mechanism confidence is lower.

## Updated Takeaway

- The local bundle does not just reward "Pepper up, buy Pepper."
- It looks more like a synthetic environment where Pepper fair is telegraphed by time-of-session and only partially revealed through the book.
- The best current design is therefore a hybrid:
  - Ash traded with restrained, real-market-like anchored maker logic,
  - Pepper traded as a competition-specific template exploit with local residual control.

## Official Narrative Truth Test

- The organiser screenshot is real official wording, not an internet rumor.
- It is only partially grounded in the local data.
- `INTARIAN_PEPPER_ROOT` is indeed "steady" in path shape:
  - the three local days are extremely repeatable,
  - the fair path is smooth,
  - and the residual around that path is small.
- But Pepper is not steady in the anchored-`EMERALDS` sense.
  - It rises by about `+1000` over each local session.
- `ASH_COATED_OSMIUM` is more microstructurally noisy than Pepper, so the "more volatile" clue is directionally fair.
- The hidden-pattern part is still weak.
  - The exploitable Ash structure is mostly anchor-plus-imbalance, not a strong session clock.

## Post-`v3` Iteration Results

### `round1_overhaul_v5.py`

Hypothesis:
- Pepper tape pressure from prior market trades contains real tactical information beyond residual alone.

Result:
- Small but consistent improvement over `v3`:
  - default `+34.0`
  - `worse` `+34.0`
  - `none` `+11.0`
  - `worse + q=0.35` `+35.0`

Interpretation:
- The trade-tape overlay is real.
- It is not the main missing engine.

### `round1_overhaul_v6.py`

Hypothesis:
- The bigger remaining miss in `v3` is the coarse Pepper phase template.

Implemented change:
- Replace the `21`-point Pepper template with a finer phase-corrected curve while preserving the broader `v5` architecture.

Result:
- Clear improvement over `v3` in every tested mode:
  - default `+601.0`
  - `worse` `+601.0`
  - `none` `+370.0`
  - `worse + q=0.35` `+483.0`
- Product delta versus `v3`:
  - `ASH`: unchanged at `45,608.0`
  - `PEPPER`: `+601.0`

Interpretation:
- The dominant post-`v3` improvement path was a better Pepper fair curve, not a heavier tactical overlay.

### `round1_overhaul_v7.py`

Hypothesis:
- Pepper residuals should recycle better when explicitly gated by current top-of-book imbalance.

Result:
- Improved over `v3`, but gave back part of the `v6` gain:
  - default `282,920.0` vs `282,974.0` for `v6`
  - `worse` `282,887.0` vs `282,941.0`
  - `none` `245,630.0` vs `245,673.0`
  - `worse + q=0.35` `259,919.0` vs `259,990.0`

Interpretation:
- The imbalance overlay was directionally sensible in research, but not worth the extra live complexity on top of `v6`.

## Updated Candidate Ranking

1. `round1_overhaul_v6.py`
   Why: best stressed score with the cleanest explanation. The main gain comes from fixing the Pepper fair curve itself.
2. `round1_overhaul_v7.py`
   Why: still strong, but weaker than `v6`; rejected because the extra tactical imbalance layer did not earn its keep.
3. `round1_overhaul_v5.py`
   Why: validates that Pepper tape pressure is a real secondary overlay.
4. `round1_overhaul_v3.py`
   Why: still a strong and simpler template-owning Pepper design, but now superseded.
5. `round1_candidate_v2.py`
   Why: lower-concentration fallback when template confidence is lower.

## External Repo Detail Used

The most useful ideas adapted from the Mark Brezina repository were architectural, not product-specific:
- reduce each market to a simpler fair object before optimizing execution,
- keep product-specific alpha engines separate,
- persist only compact running state,
- and treat execution as `take -> clear -> make` around the modeled edge rather than as one opaque block.

What was not adopted:
- any Prosperity-3 product truths,
- any old hardcoded participant assumptions,
- any round-specific thresholds as current authority.
