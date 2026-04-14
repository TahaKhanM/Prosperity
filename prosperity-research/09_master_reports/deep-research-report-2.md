# Breaking the Official Backtester Plateau in Prosperity Four Round One

## Evidence hierarchy and current unknowns

### Confirmed official facts
**[Official] Tradable products for the algorithmic continuous-book task are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`, each with a position limit of 80.** fileciteturn0file1  
**[Official] The required submission interface is a Python `Trader` class with `run(self, state)` returning `(result, conversions, traderData)`; `bid()` is only relevant in a later round and is ignored otherwise.** fileciteturn0file2  
**[Official] Matching/visibility semantics that matter for mechanism design:**
- Within each iteration, you can either (i) cross existing bot quotes (immediate match) or (ii) leave residual size as an outstanding quote that bots may trade against; if bots do not trade on it, it is cancelled at the end of the iteration. fileciteturn0file2  
- If your aggregate orders for a side would (if fully matched) breach the position limit, the exchange rejects/cancels orders for that iteration. fileciteturn0file2  
- The hosted runtime is stateless (AWS Lambda) so persistent Python globals/class fields are not safe; `traderData` is the intended persistence channel (with size constraints). fileciteturn0file2  

### Local empirical findings (your repo’s “ground truth” for what the local Rust backtester + local datasets show)
**[Local] Your current internal memo explicitly separates official facts vs local evidence and records the core local generator reads:**
- Ash looks like an anchored, replenishing-maker market around ~10,000 with short-horizon imbalance/mean-reversion; no stable time-of-session template. fileciteturn0file5  
- Pepper looks like a highly repeatable session-template latent fair with lagged/discrete quote updates; the visible book largely encodes “residual vs template”, and moderate overheat windows appear monetisable via recycle logic. fileciteturn0file5turn0file6  

**[Local] Your current “ship” is `round1_overhaul_v10.py`; it preserves the template-dominant Pepper generator and adds a template-anchored recycle/execution layer.** fileciteturn0file7turn0file8turn0file4  

### Transferable public-repo ideas (workflow/architecture/diagnostics — not Prosperity Four product truth)
**[Public → Transferable] Competition-grade strategy design benefits from explicit separation of alpha/risk/inventory/execution/portfolio, and from treating execution as the layer that makes imperfect beliefs survive reality.** This framing is central in entity["people","Mark Brezina","github author"]’s guide. citeturn1view0turn2view0turn2view2  
**[Public → Transferable] “Bot-aware” mechanics often dominate: order lifecycle is per-timestep, orders are cleared, and there can be a consistent processing order (e.g., maker liquidity first, then takers, then your bot, then more bots).** This is emphasised in entity["people","Timo Diehm","github author"]’s write-up (Prosperity Three), along with a strong warning that backtest wins can reflect simulator quirks rather than robust edges. citeturn4view1turn4view4turn4view3  
**[Public → Transferable] “Wall-based” fair value estimation: identify persistent deep-liquidity price levels (“bid wall/ask wall”) to define a robust “wall mid” rather than using the raw mid, especially when overbidding/undercutting distorts the top of book.** citeturn4view0turn7view0  
**[Public → Transferable] Tooling and ablation habits:**
- Use a visualiser to step timestamp-by-timestamp to diagnose *why* a strategy makes/loses money (inventory path, book state, trades). citeturn7view0turn8search4  
- Expect local backtest limitations (e.g., unsupported mechanics, logging causing AWS execution issues); treat this as a recurring source of “local vs official” gaps. citeturn7view2turn7view0  
- Use per-round foldered research/code/logs to keep provenance clean and enable controlled comparisons (CMU Physics; Linear Utility repos). citeturn9view0turn9view2  

### The key unknowns that plausibly explain an “official plateau”
Below are **[Unknown]** items that are *mechanism-level* (not “tweak-level”) and directly target your stated plateau problem:

**[Unknown] Pepper generator family width.** The local bundle strongly supports a near-deterministic template; *official* could preserve only the archetype (“steady”) while widening parameters: start level drift, slope schedule, template curvature, shock frequency, residual mean-reversion strength, and quote-refresh timing. Your own notes flag this as unproven. fileciteturn0file5turn0file6  

**[Unknown] Order-flow / bot sequencing / quote-refresh microstructure differences.** Even if the high-level interface matches, small differences in (i) when old orders are cleared, (ii) whether/when bots trade on your resting quote, and (iii) how/when bots refresh quotes can radically change whether a “make-heavy” monetisation layer survives. Public write-ups explicitly warn that open-source backtesters cannot fully model hidden bot nuances. fileciteturn0file2 citeturn4view4turn4view1turn9view1  

**[Unknown] Your local Pepper story may be overclaimed.** Your local docs already treat this as a live risk: the 81-knot Pepper curve may be too exact; a smoother/regularised curve may generalise better officially even if it is slightly worse locally. fileciteturn0file6turn0file7  

**[Unknown] Second edge source.** If official Pepper is “steadier” in the stationary sense (closer to tutorial EMERALDS) than in your local sample, then “own Pepper early” becomes structurally capped, and the next edge must come from (i) residual/refresh exploitation, (ii) Ash patterning, or (iii) bot-ordering exploitation that is stable across seeds. The organiser narrative explicitly suggests Pepper steady / Ash more volatile/patterned but is not a formal rule. fileciteturn0file1turn0file3  

## Critical assessment of the organiser narrative

### Intarian Pepper Root
**Claim to interrogate:** “quite steady” and “similar to EMERALDS.” fileciteturn0file1  

**In what sense it is true (supported by local evidence, but be precise):**
**[Local] Pepper is “steady” after detrending by a session-level fair:** your local notes describe Pepper as “template-plus-residual,” where most of the complexity is captured by a deterministic session fair and the residual is comparatively small and mean-reverting. fileciteturn0file5turn0file6  
**[Local] The market-structure hint that “spread stops behaving like noise and starts behaving like intention” aligns with a template + refresh world:** if quotes refresh discretely around a latent fair, the spread/state can encode whether the market is in “carry,” “discount,” or “overheated” residual regimes. This framing is consistent with the prompt-card guidance to treat spread behaviour as informative. fileciteturn0file3  

**In what sense it is misleading (and how it can cause overfitting):**
**[Local → Risk] “Steady like EMERALDS” can be misread as “stationary around a fixed anchor,” which is *not* the same hypothesis as “template drift with small residual.”** If official Pepper is closer to stationary than your local sample, strategies that monetise deterministic upward carry by max-long inventory can collapse to near-zero (or negative) edge. This is exactly the failure mode you are worried about: local wins from more exact template fitting, official plateau. fileciteturn0file5turn0file6  
**[Speculation, but grounded] The narrative may be intentionally “archetype-level”:** organisers may be signalling “low-noise / predictable” rather than “flat”. Treat it as a prior on *residual volatility* and *mean-reversion* strength, not on drift = 0. fileciteturn0file1turn0file3  

**Stylised facts to anchor this (what to measure, not vibes):**
- **Residual volatility vs raw volatility:** If Pepper is “steady,” this should hold after removing your best compact fair (template/online monotone curve).  
- **Residual half-life:** If the environment is scripted/template-like, residual should revert fast (tens of ticks), and “overheat/discount” events should be transient.  
- **Quote update granularity:** If quotes update discretely, best bid/ask should jump in preferred step sizes and exhibit refresh artefacts.

### Ash-Coated Osmium
**Claim to interrogate:** “more volatile” and may follow a “hidden pattern.” fileciteturn0file1  

**In what sense it is true:**
**[Local] Compared with a good anchor model, Ash exhibits larger short-horizon deviations and wider typical spreads than a “steady residual Pepper” world, and it demands safer execution translation.** Your internal notes say Ash remains anchored but “more volatile” in the sense that directional translations were fragile and execution is the bottleneck. fileciteturn0file5turn0file7  
**[Public → Transferable] A product can be “patterned” without being time-template-shaped:** the “pattern” may be a microstructure regime switch (liquidity thick/thin, spike-fade states) rather than a deterministic curve. This is the type of thing dashboard-driven inspection is for. citeturn3view0turn4view4  

**In what sense it is misleading:**
**[Local → Risk] “Hidden pattern” can lure you into brittle formula-to-execution translation.** Your local experience already records that better Ash fair predictors did not survive execution translation (v9 fragility). So “pattern” should be interpreted as “find a robust state machine + execution policy,” not “fit a clever predictor.” fileciteturn0file5turn0file7  

**Stylised facts to anchor this (what would make the narrative non-empty):**
- **Regime structure:** detect whether the distribution of spreads/volumes/imbalance has distinct modes with different mean-reversion speed.  
- **Spike-fade behaviour:** quantify whether large deviations from anchor revert with predictable timing/shape.  
- **Time-of-session periodicity:** test whether any spectral/seasonal component is stable across days/seeds (likely weak locally; the important question is whether official widens it).

## Deep mechanism analysis

This section is structured as: **hypothesis → precise definition → implied stylised facts → what it explains → what it fails to explain → strategy families favoured/punished → plausibility rank.**  
Labels: **[Official]** facts; **[Local]** evidence from your repo; **[Public]** analogy; **[Speculation]** unproven.

### Mechanisms for Ash-Coated Osmium

#### Anchored replenishing-maker market
**Definition:** There exists a latent anchor \(A \approx 10000\). Bots post a relatively persistent symmetric book around \(A\) with replenishment at common price levels; mid deviations are short-lived and mean-reverting.

**Implied stylised facts:**  
- Mid-price distribution tightly concentrated around \(A\).  
- Strong negative autocorrelation of 1–10 tick returns (microstructure bounce).  
- Imbalance/microprice predicts very short-horizon price movements (ticks to tens of ticks).

**Matches local evidence:**  
- Your current assumption memo explicitly calls Ash an anchored replenishing-maker market around ~10,000. fileciteturn0file5  
- Your shipped `v10` Ash sleeve is explicitly anchor-centric (constant `ASH_ANCHOR = 10000.0`) with a short-horizon fade term and microprice/“wall” terms. fileciteturn0file4  

**Explains well:** Why simple anchored market making keeps working locally; why deeper “time template” attempts didn’t. fileciteturn0file5turn0file7  

**Fails to explain:** Any stable “hidden pattern” that is not reducible to anchored mean reversion (e.g., consistent periodic regimes).  

**Favours:** take→clear→make anchored MM, with tight inventory control and small, robust leans. citeturn4view0turn2view2  
**Punishes if wrong:** any strategy that assumes stationary anchor with no regime/spike states (it will hold inventory through spikes).  

**Plausibility:** **High** (best-supported locally). fileciteturn0file5turn0file4  

#### Anchor plus transient spike-fade states
**Definition:** Same as above, but with occasional discrete “shock” states where the book shifts away from anchor (liquidity thins, spreads widen), followed by predictable fade back.

**Stylised facts:**  
- Conditional on a “shock indicator” (large \(|mid-A|\) or large \(|\Delta mid|\)), subsequent returns are mean-reverting and spreads/volumes shift.  
- A regime classifier improves execution safety.

**Matches local evidence:**  
- `v10` explicitly computes a `shock` boolean from large anchor deviation or large 1-step return and changes take/make sizing accordingly. fileciteturn0file4  
- Your notes say more directional Ash logic failed in stressed modes; a regime-aware execution layer is exactly the remedy. fileciteturn0file7  

**Explains well:** Why “better fair” didn’t translate: shocks punish aggressive execution even if the predictor is right on average. fileciteturn0file7  
**Fails to explain:** Any longer-horizon periodicity (if that exists officially).  

**Favours:** state-machine MM: normal (tight) vs shock (widen/defend/flatten).  
**Punishes if wrong:** overcomplicated regime logic that reduces fill rate without reducing adverse selection.  

**Plausibility:** **High** (already embedded in shipped logic). fileciteturn0file4turn0file7  

#### Liquidity-regime switching (hidden pattern as liquidity schedule)
**Definition:** The “pattern” is not in the latent fair, but in liquidity/quote refresh cadence; the anchor stays fixed, but the spread/volume schedule is time-structured or state-structured.

**Stylised facts:**  
- Predictable clusters of wide spreads / missing-side books / volume walls at certain times or after certain trade-flow signatures.  
- Profit comes from adapting *execution aggressiveness* to liquidity regime, not from predicting fair drift.

**Support:**  
- Prompt cards hint that “spread behaviour” can encode “intention” and that orders should “feel like they belong,” which in a bot market often translates to “don’t be the obvious impatient taker in thin regimes.” fileciteturn0file3  
- Public writeups stress microstructure-first thinking and dashboard-based regime discovery. citeturn3view0turn4view4  

**Explains well:** If official backtester differs by liquidity schedule, local fair tweaks plateau while execution-adaptation would generalise.  
**Fails to explain:** Purely price-level patterns without liquidity changes.

**Favours:** execution policy redesign (dynamic widths/sizes, selective taking).  
**Punishes if wrong:** undertrading (missing easy anchored edge).

**Plausibility:** **Medium** (consistent with “pattern” wording; not proven locally). fileciteturn0file1turn0file5  

#### Hidden periodic/scripted behaviour in fair
**Definition:** There exists a periodic or pseudo-periodic component in Ash latent fair (beyond anchored MR).

**Stylised facts:**  
- Stable cross-day phase alignment (same time-of-session component across days/seeds).  
- A low-dimensional sinusoid basis in “progress” predicts returns beyond imbalance/microprice.

**Local status:** your own notes currently do **not** support a stable time-template for Ash. fileciteturn0file5  
**Plausibility:** **Low–Medium** locally, but could be **Medium** officially if organisers widened the generator.

### Mechanisms for Intarian Pepper Root

#### Exogenous session-template latent fair
**Definition:** There is a deterministic monotone function \(F(t)\) (possibly day-shifted) that defines “true” Pepper value. Quotes are rendered around \(F(t)\) with small noise; observed mid follows \(F(t)\) closely.

**Stylised facts:**  
- After shifting by an inferred open level and mapping time to progress, days overlay almost perfectly.  
- Residual \(mid - F(t)\) has small variance and fast mean reversion.  
- A monotone piecewise-linear approximation with modest knots fits well.

**Matches local evidence:**  
- Your assumption memo and signal ranking both describe Pepper as an “extremely repeatable rising session path” and discuss knot-count ablations (81 vs 61) specifically as a regularisation axis. fileciteturn0file5turn0file6  
- `v10` implements exactly this: infer `open_mid`, define `template_fair = open_mid + interp_template_offset(progress)`, then classify `residual` into modes (opening/discount/overheated/carry). fileciteturn0file4  

**Explains well:** Why “own Pepper early” dominates local PnL and why the next gains came from “recycle around template” rather than further curve fitting. fileciteturn0file7turn0file8turn0file6  

**Fails to explain:** The official plateau **if** official Pepper is materially more stationary or the template family is wider than your offsets list.

**Favours:** template-carry + residual MR state machine.  
**Punishes if wrong:** max-long carry that assumes deterministic upward drift (catastrophic if drift shrinks/reverses).  

**Plausibility:** **High locally**, **unknown officially**. fileciteturn0file5turn0file6turn0file4  

#### Template plus lagged/discrete quote bots (refresh artefact model)
**Definition:** Same latent \(F(t)\), but quotes only refresh discretely (e.g., step sizes) and can temporarily overshoot/undershoot \(F(t)\); residual spikes are mostly quote-refresh artefacts that mean-revert quickly.

**Stylised facts:**  
- Best bid/ask move in preferred jump sizes (not continuous drift).  
- “Overheated” or “discount” residual states are short-lived (tens of ticks), with strong mean reversion.  
- Market trades may precede book adjustments (lag).

**Matches local evidence:**  
- Your memo explicitly claims Pepper books are short refresh artefacts and that trades precede later quote adjustments, consistent with lagged updates. fileciteturn0file5  
- `v10` computes `trade_ema` from market trades and uses it as a small bias term, implicitly treating market trades as informative about near-term state. fileciteturn0file4  

**Explains well:** Why a recycle layer can add value even when already full: residual spikes mean-revert while the template continues (so “sell residual, rebuy residual” improves without abandoning carry). fileciteturn0file7turn0file4  

**Fails to explain:** A world where residual spikes are rare or do not revert (official could widen noise).  

**Favours:** generator+execution split: keep generator anchored on template, execute residual MR with guarded thresholds. fileciteturn0file6turn0file4  
**Punishes if wrong:** overly aggressive recycling that churns inventory and loses carry.

**Plausibility:** **High locally**, and crucially **more likely to generalise** than “exact curve hardcode,” because it relies on *mechanism* (refresh + MR), not exact offsets. fileciteturn0file6turn4view4  

#### Piecewise regime process (broader family than one curve)
**Definition:** \(F(t)\) is not fixed; it is sampled from a family of monotone shapes per run/day (e.g., random knot perturbations, slope schedule regimes), while still “steady” in the sense of low residual noise around the sampled \(F(t)\).

**Stylised facts:**  
- Fitting a single global curve across days works locally (your bundle), but a regularised low-parameter shape with online calibration would be more robust out-of-sample.  
- Official evaluation would punish exact-curve hardcodes but reward shape-constrained adaptive fits.

**Local support:** You already run this exact “regularisation control” logic direction: `v11` as a smoother-template control versus `v10` as best ship. fileciteturn0file7turn0file8turn0file6  

**Explains well:** The *plateau phenomenon*: local improvements come from exploiting idiosyncratic template details, but official holds steady because the true generator is a family, not your single curve. fileciteturn0file6turn4view4  

**Plausibility:** **Medium–High** as the leading explanation for “local improves, official plateaus.” fileciteturn0file6turn0file5  

## Formula search and compact models

This section proposes **explicit candidate formulas** designed to be (i) compact enough to implement in a single trader file, (ii) anchored in mechanism expectations, and (iii) regularised to generalise to official.

### Ash fair-value and control models

#### Anchor + robust book mids + microprice + 1-step fade
**Model (close to what `v10` already encodes, but written explicitly):**

Let:
- \(A = 10000\) (anchor)  
- \(mid_t = \frac{bid^1_t + ask^1_t}{2}\)  
- \(mm10_t\) = mid of the nearest bid/ask levels with volume ≥ 10 (fallback to “wall mid”)  
- \(wall_t = \frac{wallBid_t + wallAsk_t}{2}\) using the max-volume levels (within your available depth)  
- \(micro_t = \frac{bid^1_t \cdot volAsk^1_t + ask^1_t \cdot volBid^1_t}{volBid^1_t + volAsk^1_t}\)  
- \(r_t = mid_t - mid_{t-1}\)

Define a clipped deviation:
\[
d_t = clip(mm10_t - A,\,-d_{max},\,d_{max})
\]
micro-bias:
\[
m_t = clip(micro_t - mid_t,\,-m_{max},\,m_{max})
\]
fade term:
\[
f_t = clip(-\lambda r_t,\,-f_{max},\,f_{max})
\]

Then:
\[
\widehat{fair}_t = A + \alpha d_t + \beta m_t + \gamma f_t
\]

**Role of terms:**
- \(d_t\): “where the thicker book thinks the anchor is” (robust to small top-of-book noise).  
- \(m_t\): queue/imbalance proxy (microprice leans slightly towards the side with less displayed volume).  
- \(f_t\): automatic mean-reversion after discrete jumps (refresh artefact fade).  

**Why it might generalise:** It is anchored on a constant \(A\) and uses only universal microstructure primitives (robust mid, microprice, jump-fade), matching both public “wall mid” philosophy and your local Ash diagnosis. citeturn4view0turn7view0 fileciteturn0file5turn0file4  

**How it could fail:** If official Ash “pattern” is not anchored MR but a drifting latent fair or a regime pattern that changes \(A\), then constant-anchor logic underfits and will be systematically wrong in trend phases. fileciteturn0file1turn0file5  

#### Regime-gated execution widths (the part that likely matters more than \(\widehat{fair}\))
Instead of searching for a smarter \(\widehat{fair}\), make execution robust:

Define a shock score:
\[
shock_t = \mathbf{1}\{|mid_t-A|\ge \Delta_A \ \text{or}\ |r_t| \ge \Delta_r\}
\]
Then set quoting widths and take thresholds:
\[
edge^{take}_t = edge^{take}_{base} - c_{shock} \cdot shock_t
\]
\[
width^{make}_t = width^{make}_{base} + w_{shock} \cdot shock_t + w_{inv}\cdot |pos_t|
\]

This is exactly the style of “execution makes imperfect signals survive reality” argued in the public guides, and it matches your own conclusion that Ash improvements failed via fragile execution translation. citeturn2view2turn2view0 fileciteturn0file7turn0file4  

### Pepper fair-value and control models

#### Regularised monotone template family
Replace the exact offset list with a small-parameter monotone model that is calibrated online.

Let \(p \in [0,1]\) be session progress, \(open\) be inferred from early mid/book, and constrain \(F(p)\) to be monotone increasing.

**Candidate model A (power curve):**
\[
F(p) = open + A \cdot p^{\nu}
\]
Parameters: \(A>0\) (total rise), \(\nu>0\) (curvature).

Online update (RLS-like, but simple):
- Estimate \(open\) from the first \(N\) ticks (median of mid or wall mid).  
- Track \(A\) as \(A_t = clip(mid_t - open, 0, A_{max}) / p\) for \(p>\epsilon\) then smooth with EMA.  
- Track \(\nu\) coarsely by matching two quantiles (e.g., \(p=0.25,0.75\)).

**Candidate model B (few-knot monotone spline):**
Choose knots \(0 = p_0 < p_1 < ... < p_K=1\) (e.g., \(K=7\) or \(K=11\)). Parameterise offsets \(y_k\) with constraint \(0=y_0 \le y_1 \le ... \le y_K\).  
Then:
\[
F(p) = open + \text{lininterp}(p;\{(p_k, y_k)\})
\]
Online update: every \(M\) ticks, project observed \((p, mid-open)\) into a monotone least-squares fit (can be approximated cheaply by updating only neighbouring knots + enforcing monotonicity by pooling adjacent violators).

**Why this might generalise officially:** It treats the template as an archetype (monotone, smooth, low-noise residual) without committing to your single 81-point curve. This aligns with your own “v11 regularised control” motivation. fileciteturn0file6turn0file7  

**How it could fail:** If official Pepper is stationary (no monotone drift), the model will hallucinate drift and push you into max-long carry. Mitigation must be explicit: a hypothesis test for “total rise is significant.” fileciteturn0file1turn0file5  

#### Template + residual correction + refresh/overshoot fade (compact, implementable)
Keep the generator \(F(p)\) but trade on residual \(e_t = mid_t - F(p)\).

A compact control fair:
\[
\widehat{fair}_t = F(p_t) + \kappa \cdot EMA(e_t;\tau_e) + \eta \cdot EMA(flow_t;\tau_f)
\]
Where \(flow_t\) is a signed market-trade flow score (as in `v10`). fileciteturn0file4  

**Overshoot-fade trigger (mechanism-first):**
Define a refresh event indicator (conceptually): both bid and ask jump in the same direction by ≥ \(J\) ticks within one timestep.
Then:
- after an “up refresh,” expect short-horizon negative drift in residual; after a “down refresh,” expect positive drift in residual.  
This supports a **residual fade** action rule:
\[
if\ e_t > e_{hi}\ \text{and refreshUp}: \ \text{increase sell aggressiveness / recycle}
\]
\[
if\ e_t < -e_{lo}\ \text{and refreshDown}: \ \text{increase buy aggressiveness / reacquire}
\]

**Why it might generalise:** It is not tied to the exact curve; it is tied to quote-refresh microstructure and residual mean reversion, which are precisely the kinds of “simulation-handling order flow” effects top teams explicitly exploited after understanding the environment. citeturn4view1turn4view4  

**How it could fail:** If official bots refresh smoothly (no discrete overshoot/undershoot), refresh flags become noise and you churn.

#### Carry-vs-recycle decision rule (residual-domain, not absolute-price-domain)
A more correct “recycle value” objective in a drifting template market is:

If you are long, selling now and rebuying later is beneficial if the expected **residual drop** outweighs spread costs, even if absolute price rises.

Define:
\[
e_t = mid_t - F(p_t)
\]
Choose a horizon \(H\) and predict expected residual reversion:
\[
\mathbb{E}[e_{t+H} \mid e_t] \approx \rho e_t,\ \ 0<\rho<1
\]
Then expected residual capture from recycling some quantity is:
\[
\Delta e \approx e_t - \rho e_t = (1-\rho)e_t
\]
Recycle if:
\[
(1-\rho)e_t \ge c_{spread} + c_{slip}
\]
This reframes “recycle economics” in the correct coordinate system, and it matches why `v10` makes recycle decisions anchored to template residual rather than raw mid. fileciteturn0file4turn0file7  

## Where the current local best is probably leaving money on the table

Assuming the `v10` family already captures “own Pepper early” and adds moderate residual recycle, these are the most plausible remaining gaps that can break an official plateau.

### Pepper: the most likely remaining edge is *robustness*, not more curve-fitting
**[Local] Your own research already flags that the key unproven piece is whether official preserves the exact local Pepper curve or only the broader archetype.** fileciteturn0file5turn0file6  
So the next step is not “make 81 knots even more exact,” but:

**[Gap] Add a hypothesis test and fallback policy.**  
Mechanism-first design: before committing to max-long carry, estimate whether Pepper has a statistically significant monotone drift this session:
- estimate \( \Delta = F(1)-F(0)\) online; if \( \Delta < \Delta_{min}\) by mid-session, shift to a stationary “anchored MR” Pepper policy (EMERALDS-like).  
This directly targets the organiser’s ambiguity (“steady like EMERALDS”) and is the cleanest defence against official-vs-local mismatch. fileciteturn0file1turn0file6  

**[Gap] Reacquire logic symmetry.**  
`v10`’s innovation is selling when full and moderately overheated relative to template. The symmetric missing money is often: *after you sell*, if the residual mean-reverts quickly, you need a “fast reacquire” state with different execution than the original “build inventory early” state. Your current docs frame this as carry-vs-recycle policy engineering, not fair estimation. fileciteturn0file6turn0file7  

### Pepper: phase-specific policies (open / carry / recycle / de-risk)
**[Local] `v10` already computes `progress` and uses it to gate recycle aggressiveness.** fileciteturn0file4  
The likely next money:
- **Mid-session:** aggressive residual monetisation (highest number of refresh events + time left for reacquire).  
- **Late-session:** de-risk: prefer flattening residual risk rather than chasing last recycle.

This is aligned with the prompt card’s warning against “orders trying too hard” — in late-session thin liquidity, over-eager quotes are punished. fileciteturn0file3  

### Ash: still plausibly underexploited, but only via safer execution layers
**[Local] Your execution-risk report shows almost all incremental gains came from Pepper; Ash stayed unchanged in the chosen ship, explicitly for safety.** fileciteturn0file7turn0file8  
So “money left” in Ash is real, but the constraint is robust translation:

**[Gap] Add an Ash regime gate that only turns on extra aggression when the environment is demonstrably safe.**  
Example: only widen quoting or increase take size when:
- spread is tight AND both sides present AND book depth is above threshold AND recent adverse selection is low.

This is exactly the “alpha/risk/inventory/execution must be designed together” warning from public guides. citeturn2view0turn2view2  

### Portfolio-level allocation (small, but could matter if Pepper edge shrinks officially)
If official Pepper drift is weaker, you need a portfolio rule to prevent “max-long Pepper” from starving Ash when Ash has better opportunity quality (e.g., frequent anchored mispricings with safe liquidity). This is “portfolio management” in the Prosperity sense (allocation across engines), not real-world multi-asset investing. citeturn2view3turn2view2  

## Public-repo transfer map and breakthrough hypotheses

### Transfer map: what to copy, what not to copy

**From Mark Brezina’s guide (Ctrl-Alt-DefeatTheMarket):**
- **Transferable:** Five-part decomposition (alpha/risk/inventory/execution/portfolio), and the insistence that execution design determines whether alpha survives. citeturn1view0turn2view2turn2view3  
- **Not transferable:** Any tutorial product specifics or implied mapping of products across years. (He explicitly notes Round One was unknown at time of writing.) citeturn1view0  
- **Local belief challenged:** “More signal branches = more profit.” The decomposition forces you to identify whether you are bottlenecked on generator belief vs execution translation — your Ash experience says you are. fileciteturn0file7  

**From Timo Diehm’s Frankfurt Hedgehogs write-up:**
- **Transferable:**  
  - “Wall mid” as a robust fair proxy derived from persistent liquidity walls. citeturn4view0  
  - A strong warning: open-source backtesters can’t replicate subtle bot behaviour; use controlled tests to learn the environment, not just optimise. citeturn4view4turn4view0  
  - Mechanism obsession: understand timestep order lifecycle and bot sequencing; edges can come from how the simulator processes order flow. citeturn4view1turn4view2  
- **Not transferable:** Prosperity Three-specific “hardcoding” exploit details as a direct recipe (rules differ; also disallowed/ethically fraught). Use only as a cautionary tale about “bot behaviour replication” risk and the value of fallbacks. citeturn4view3  
- **Local belief challenged:** “Local curve exactness is the edge.” Their backtesting section argues that strategies depending on bot interactions must be validated in the official environment because bot nuance is not fully observable. This mirrors your plateau issue almost exactly. citeturn4view4  

**From CarterT27’s Alpha Animals repo:**
- **Transferable:**  
  - Identify consistent market-maker liquidity to reduce noise and estimate a reliable fair (their Round One Kelp approach). citeturn7view4turn7view0  
  - Tooling discipline: visualiser-driven debugging; beware AWS/lambda issues and logging constraints. citeturn7view0turn7view2  
- **Not transferable:** Prosperity Three product lineup and their exact parameter values. citeturn7view4  
- **Local belief challenged:** “Local backtester is enough.” They explicitly describe gaps between backtester support and official mechanics causing real losses. citeturn7view2turn7view0  

**From CMU Physics and Linear Utility repos (workflow discipline):**
- **Transferable:** Per-round provenance: keep EDA, research, and strategy versions together; this enables proper counterfactual testing and prevents “parameter drift” from masquerading as progress. citeturn9view0turn9view2  
- **Not transferable:** Any bot behaviour “truths” from prior years.  
- **Local belief challenged:** “One main ship is enough.” These repos emphasise tooling and iteration, consistent with your need for ablation/diagnostics that distinguish overfit from genuine generator understanding. citeturn9view0  

### Breakthrough hypotheses (eight to twelve)

Each hypothesis includes: **why it could improve official**, **what confirms**, **what falsifies**, **minimal redesign test**.

**Hypothesis A: Official Pepper is stationary-ish (EMERALDS-like), and your local template-carry edge is mostly an artefact of the provided sample bundle.**  
- Why it helps: Explains the plateau: local template improvements don’t move official because the main edge doesn’t exist officially. fileciteturn0file1turn0file6  
- Confirms: In official backtests, Pepper mid does not exhibit a large net rise; or your mark-to-market does not benefit from holding long.  
- Falsifies: Official Pepper shows consistent monotone drift similar magnitude.  
- Minimal redesign: Add an online drift test; switch between “template carry” and “stationary anchored MR” Pepper modes by mid-session.

**Hypothesis B: Official Pepper is still template-like, but the template is sampled from a wider family (shape/curvature varies), so the 81-knot hard curve overfits while a low-knot/parametric monotone model generalises.**  
- Why it helps: Directly matches your own “v11 as regularised control” framing and the plateau story. fileciteturn0file6turn0file7  
- Confirms: A regularised template (few knots/power curve) improves official even if it slightly harms local.  
- Falsifies: Exact curve stays best on official too.  
- Minimal redesign: Swap in a 7–11-knot monotone spline with online calibration; keep recycle logic identical.

**Hypothesis C: The missing official edge is not “carry,” it is “refresh artefact mean reversion” (residual spikes), and your current recycle triggers are too conservative / asymmetric.**  
- Why it helps: Refresh artefacts are simulator-mechanism and thus more likely stable across seeds than the exact drift curve. citeturn4view1turn4view4  
- Confirms: Official gains appear when you add a symmetric “sell-overheat + rebuy-after-revert” controller with refresh gating.  
- Falsifies: Recycle/reacquire increases churn without improving PnL.  
- Minimal redesign: Add a “reacquire state” after recycle, keyed on residual crossing back below a threshold.

**Hypothesis D: Local/official gap is dominated by bot sequencing differences (who trades after you in the timestep), so make-heavy strategies are miscalibrated.**  
- Why it helps: Public writeups emphasise timestep order lifecycle; local backtesters often can’t replicate bot nuance. citeturn4view1turn4view4turn9view1  
- Confirms: A taker-heavy variant (mostly crossing when edge is large; minimal passive quoting) improves official stability.  
- Falsifies: Maker-heavy remains superior on official.  
- Minimal redesign: Create a “taker-first” Pepper and Ash variant: take favourable quotes, otherwise place minimal passive orders.

**Hypothesis E: Ash contains the true “second edge” officially (pattern/regime schedule), but your safe anchored MM underuses it.**  
- Why it helps: Organiser narrative explicitly hints at hidden pattern for Ash. fileciteturn0file1  
- Confirms: In official runs, Ash contribution rises significantly when you add regime-gated aggression.  
- Falsifies: Ash improvements remain flat; Pepper dominates.  
- Minimal redesign: Add a 2-regime Ash execution gate (normal vs shock/liquidity-thin) and let the “normal” regime quote tighter and larger.

**Hypothesis F: Official penalises “urgent-looking” execution more than local (adverse selection), so your aggressive actions donate edge.**  
- Why it helps: Prompt card warns against eager/too-generous orders; could be hinting at bot opponents that punish urgency. fileciteturn0file3  
- Confirms: Reducing aggressiveness (smaller sizes, less crossing, more patience) improves official even if it lowers local.  
- Falsifies: Aggression correlates with higher official PnL.  
- Minimal redesign: Add a “calm execution” mode: cap per-tick size; avoid crossing unless edge > threshold; stagger entries.

**Hypothesis G: Your Pepper strategy is overconcentrated; official variance punishes max-long exposure when the drift is not guaranteed.**  
- Why it helps: If official template occasionally stalls/reverses, concentration dominates expected value. citeturn2view3turn2view0  
- Confirms: A lower-target-long policy (e.g., target 40–60) with better residual trading beats max-long officially.  
- Falsifies: Always-max-long remains best.  
- Minimal redesign: Portfolio allocator that scales Pepper target by drift confidence.

**Hypothesis H: A compact diagnostic-driven policy generalises better than deeper conditional branching.**  
- Why it helps: Public champions emphasise simple robust strategies and disciplined scepticism of “works in backtest” complexity. citeturn4view4turn1view0  
- Confirms: A model with fewer moving parts but explicit drift test + residual MR beats intricate heuristics.  
- Falsifies: Complexity systematically improves official.  
- Minimal redesign: Build a “minimal mechanistic Pepper”: (i) monotone drift estimator, (ii) residual MR controller, (iii) basic inventory guard.

## Candidate strategy families and a research-to-implementation plan

### Candidate strategy families (six to ten)

Each family is given as: **market hypothesis → generator hypothesis → fair model → inventory policy → execution policy → why it beats → why it generalises → failure mode**.

#### Regularised-generator Pepper with drift test (primary “plateau breaker” candidate)
- Market hypothesis: Pepper has low residual noise but the drift template varies by run; sometimes drift is weak.  
- Generator hypothesis: monotone drift family + residual MR; not a single fixed curve. fileciteturn0file6  
- Fair model: \(F(p)=open + A p^{\nu}\) (or K-knot monotone spline), updated online; residual \(e=mid-F(p)\).  
- Inventory: target-long scales with drift confidence; if drift confidence low, target near 0 (stationary MR mode).  
- Execution: take favourable quotes vs \(F(p)\); recycle/reacquire on residual thresholds, not absolute.  
- Why it might beat current best: it directly attacks the “exact local curve” overfit channel that plausibly causes the official plateau. fileciteturn0file5turn0file6  
- Why it might generalise: it encodes archetype constraints (monotone/steady) without hardcoding the exact realised path.  
- Failure mode: if Pepper drift is actually fixed and known (official matches your curve), regularisation sacrifices edge.

#### Pepper recycle–reacquire state machine (execution redesign, same generator)
- Market hypothesis: residual spikes are refresh artefacts that mean-revert quickly; you can harvest them repeatedly while maintaining carry.  
- Generator hypothesis: template + discrete refresh overshoot. fileciteturn0file5turn0file4  
- Fair model: keep `v10` template (or regularised one) but build explicit states:
  - **Build**: accumulate to target-long.  
  - **Carry**: hold.  
  - **Recycle**: sell tranche when \(e \in [e_1,e_2]\) and buyflow absent.  
  - **Reacquire**: rebuy tranche when \(e\) returns below \(e_{re}\) or after down-refresh.  
  - **De-risk**: late session flatten residual exposure.  
- Inventory: maintain a “core” carry position + “satellite” tranche traded for residual.  
- Execution: tranche sizes calibrated to spread; avoid large urgent orders (prompt hint). fileciteturn0file3  
- Why beat: monetises symmetric residual MR rather than only “sell when overheated.”  
- Why generalise: relies on MR, not exact curve.  
- Failure mode: if residual doesn’t revert reliably in official, churn losses dominate.

#### Ash safe regime-gated market making
- Market hypothesis: Ash is anchored but has occasional shock/liquidity-thin regimes causing adverse selection. fileciteturn0file5turn0file7  
- Generator hypothesis: anchor + spike-fade + liquidity regimes.  
- Fair model: anchor + robust mid + microprice + fade (as above).  
- Inventory: strict soft caps; reduce size when shock.  
- Execution: in normal regime, quote tighter and larger; in shock regime, widen, prioritise flattening, reduce passive exposure.  
- Why beat: extracts more of Ash’s anchored edge without the fragility you saw in v9-style directional translation. fileciteturn0file7  
- Why generalise: regime gating is mechanism-based and robust to parameter shifts.  
- Failure mode: misclassifying regimes reduces participation and PnL.

#### Refresh-aware exploitation layer (competition-specific, but mechanism-grounded)
- Market hypothesis: discrete quote-refresh events create predictable short-horizon mean reversion (bounce) in both products.  
- Generator hypothesis: refresh overshoot is structural. citeturn4view1turn4view0  
- Fair model: existing; this layer only adjusts aggressiveness after detected refresh.  
- Inventory: only trade small “tactical” size on refresh to avoid overfitting.  
- Execution: after up-refresh, avoid buying and consider small sells if long; after down-refresh, avoid selling and consider small buys if short.  
- Why beat: adds a second, generator-independent microstructure edge.  
- Why generalise: simulator refresh mechanics are likely stable across seeds.  
- Failure mode: refresh detection is noisy; you add friction without consistent benefit.

#### Lower-concentration “robust official” portfolio
- Market hypothesis: official Pepper may not deliver deterministic carry; diversification across products matters.  
- Generator hypothesis: Pepper drift uncertain; Ash anchored.  
- Fair model: regularised Pepper + robust Ash anchor.  
- Inventory: cap Pepper target below 80 unless drift confidence high; allocate risk budget between products.  
- Execution: calmer, smaller, fewer branches (to reduce adverse selection and local-only quirks). citeturn2view0turn2view2  
- Why beat: improves worst-case official outcomes if Pepper story is wrong.  
- Why generalise: less reliance on one archetype and one dataset.  
- Failure mode: if Pepper carry is real, you underinvest and lose rank.

#### Full redesign: two-engine per product with strict interfaces
- Market hypothesis: the plateau is architectural: strategy upgrades improved local because they implicitly changed execution, but official needs deliberate separation + ablation.  
- Generator hypothesis: unknown mix; must remain robust.  
- Fair models: (i) minimal robust fair, (ii) residual and regime diagnostics.  
- Inventory: shared risk module enforcing soft/hard limits.  
- Execution: shared execution module implementing take→clear→make with regime-based parameters. citeturn4view0turn2view2  
- Why beat: enables clean ablations to identify what is real vs local-only; accelerates discovery more than any single heuristic tweak.  
- Why generalise: removes brittle coupling of belief and execution.  
- Failure mode: time cost; may not outperform quickly without disciplined testing.

### Recommended research-to-implementation agenda

This plan is prioritised to answer your core question: *why local upgrades keep helping locally while official plateaus* — and to build the next trader that can break it.

**Top strategy directions (prioritised):**
1. **Pepper generator regularisation + online drift test + fallback** (directly targets the likely overfit axis and organiser ambiguity). fileciteturn0file6turn0file1  
2. **Pepper recycle–reacquire state machine (residual-domain), with explicit “core vs satellite” inventory** (targets monetisation that is more mechanism-stable than exact curve fit). fileciteturn0file7turn0file4  
3. **Ash regime-gated execution tightening (not smarter prediction)** (targets the hinted “pattern” safely, consistent with your v9 lessons). fileciteturn0file7turn0file1  

**Single best next trader to build first:**  
**A “Pepper regularised generator + drift test + unchanged `v10` recycle logic” variant.**  
Rationale: it isolates the single most plausible cause of the plateau (overfit template shape) while keeping the monetisation layer and most execution behaviour intact, giving the cleanest attribution. fileciteturn0file6turn0file7turn0file4  

**Single best ablation to run first:**  
**Hold execution fixed, change only the Pepper generator family:**  
- Variant 1: current 81-knot offsets (baseline).  
- Variant 2: 7–11-knot monotone spline (offline fit on early ticks, then slow updates).  
- Variant 3: power/logistic curve with 2 parameters.  
Then compare official PnL across these variants. This is exactly the “controlled algorithm tests to learn environment behaviour” discipline described by top teams. citeturn8search11turn4view4  

**Single best diagnostic to distinguish local overfit from genuine generator understanding:**  
**Out-of-sample “shape sensitivity” curve:** plot official PnL vs template smoothness/parameter count while keeping execution constant.  
- If official is flat (plateau) while local improves with exactness, you’ve diagnosed template overfit.  
- If both improve similarly, you have a real mechanism edge and should invest in execution monetisation instead.

**Ship/reject metrics (specific, competition-relevant):**
- **Official PnL uplift vs baseline** (obvious).  
- **PnL decomposition by product** (does the change move Pepper or Ash?). fileciteturn0file7  
- **Inventory path statistics:** time to reach large |pos|, time spent near limits, and number of inventory “churn cycles” (sell then rebuy) in Pepper; excessive churn is a red flag if it isn’t producing uplift. fileciteturn0file7turn0file4  
- **Execution quality proxies:** fraction of trades executed by crossing vs by being hit; if official punishes passive fills, you should see a strong dependence here (ties back to bot sequencing uncertainty). fileciteturn0file2 citeturn4view1turn4view4  

Finally, when you hand this to a coding agent, retain the provenance discipline in your repo prompt-engineering context: keep official facts separate from local evidence and include explicit validation steps/ablations in the Codex prompt workflow. fileciteturn0file0