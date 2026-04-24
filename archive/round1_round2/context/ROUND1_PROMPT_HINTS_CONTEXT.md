# Prosperity 4 Round 1 Prompt Hints Context

## Purpose
This file extracts and structures all useful competition-relevant information visible in the provided Round 1 prompt screenshots.

It is intended as a **context / handoff file** for strategy work, auction work, and prompt-engineering for Codex.

## Source provenance
Source screenshots provided by the user:
- `Screenshot 2026-04-14 at 13.19.13.png`
- `Screenshot 2026-04-14 at 13.19.32.png`
- `Screenshot 2026-04-14 at 13.19.42.png`

These appear to be in-competition narrative prompt cards labeled:
- `Spotting trends`
- `Strategic orders`
- `Auction dynamics`

## Interpretation policy
Treat the screenshots as a mix of:
1. **Directly observed wording** from the game UI
2. **Soft strategic hints** embedded in narrative language
3. **Not formal rules**, unless the content clearly states a mechanism

Use them as signal-rich guidance, but do **not** treat them as stronger authority than official round docs, exchange rules, position limits, or interface requirements.

---

# 1. Direct text extraction

## 1.1 Spotting trends

> Oh. This part. Everyone suddenly wants to be a trend spotter.
>
> Look, trends are not always loud. The good ones rarely are, actually. They start as a vibe. A feeling. A slight imbalance. Something that lingers just a bit longer than it should. You either notice it, or you don't. That's kind of it.
>
> Take Intarian Pepper Root. Slow growth. Predictable supply. No drama. And yet the market reacts anyway. Subtle shifts. Up. Down. Whatever. Repeating moods. You can almost feel when people start leaning one way without really committing to it.
>
> You could stare at the data all day and call it analysis. Or you could notice when the spread stops behaving like noise and starts behaving like intention. That is usually when something is forming.
>
> How to spot it? Don't look at me. If I tried to explain it, I would probably bore myself to sleep before I finish the first sentence. Just... watch closely. When the same thing keeps happening and no one reacts yet, that's usually your cue.
>
> Anyway. Slow markets are nice, if you ask me.
>
> Was that it?

## 1.2 Strategic orders

> Okay. So you have figured out a fair value? Good for you. Now this is the part where people get eager. Orders that are trying too hard. Prices that lean forward. Sizes that scream "pick me". It's... yuck. You know. Don't do that. Just don't.
>
> Keep that fair value in the back of your head. Then look at what everyone else is offering and ask yourself this: does my order feel intentional and calm, or does it feel rushed and like... whatever?
>
> Because markets feel that stuff, you know. I've been laughed at for saying that. But I know who'll be laughing last... Yeah, yeah. Markets don't “feel” that literally, but it shows. That's all I'm saying. An order that's a little too generous. A bid that's oddly urgent. A size that doesn't match the mood. Those stand out in a bad way.
>
> If you want to get matched, your order should feel like it belongs. Not like it's begging. Adjust the price. Nudge the size. Wait half a beat longer if you have to. When it stops feeling awkward and starts feeling right, you're close.

## 1.3 Auction dynamics

> These auctions are pretty chill. Everyone has already placed their orders. The board is frozen. No more random order vibes. Just read the room, make one last move and let everyone else pretend they meant for this to happen all along.
>
> I don't know why I would repeat something this obvious, but your final order actually matters here, you know. It affects the auction clearing price itself. That's the part people forget. Some might think they're just participating, like NPCs, when they could just as well act like the main character and nudge the outcome instead.
>
> Simulations? Well. I guess if you want to do them. Fine by me.
>
> You'll probably see in those numbers what I already sensed. But yeah. Go ahead. Change the size. Shift the price. Watch where things start to bunch up. Where the outcome keeps snapping back to the same spot.
>
> That's usually when it clicks. Not because you solved it, but because the market stops arguing with you.

UI footer visible in the final auction screenshot:

> There are no more prompts available for this round. You can revisit your log until new prompts become available in the round.

---

# 2. High-confidence facts directly supported by the screenshots

## 2.1 Product-specific hint
- `Intarian Pepper Root` is explicitly referenced.
- It is described as having:
  - **slow growth**
  - **predictable supply**
  - **no drama**
- Despite that, the market still shows:
  - **subtle shifts**
  - **up/down movement**
  - **repeating moods**
  - participants **leaning one way without fully committing**

## 2.2 Market-structure hint
- The screenshots explicitly suggest that **spread behavior can carry information**.
- Specifically, the text says to notice when the spread stops looking like random noise and starts looking like **intention**.

## 2.3 Order-placement hint
- The screenshots explicitly warn against:
  - overly eager pricing
  - overly large or conspicuous size
  - quotes that look too generous or urgent
- They explicitly recommend:
  - anchoring on a **fair value**
  - adjusting **price**
  - adjusting **size**
  - being patient / waiting slightly longer when needed

## 2.4 Auction-mechanics hint
- The screenshots explicitly say:
  - the auction board is **frozen** after orders are placed
  - a **final order** still matters
  - the final order can affect the **auction clearing price**
- They explicitly recommend:
  - running **simulations**
  - varying **size** and **price**
  - looking for where outcomes **bunch up**
  - looking for where the auction outcome **snaps back to the same spot**

## 2.5 Meta signal
- Prompt supply appears limited by round.
- At the time of the screenshot, there were **no more prompts available for this round**.

---

# 3. Competition-relevant implications

## 3.1 Implications for algorithmic trading in Round 1

### Intarian Pepper Root
Most likely useful takeaway:
- This product may look stable on a coarse view, but there may still be exploitable **small, repeated short-horizon behavioral patterns**.
- The likely useful signal family is not “large obvious trend” but:
  - subtle drift
  - repeatable micro-regimes
  - order-book imbalance persistence
  - spread-state persistence
  - repeated one-sided leaning before full repricing

Strong implication:
- A strategy that only treats Pepper Root as perfectly static may leave money on the table.
- A strategy that overreacts to noise may also be wrong.
- The likely sweet spot is detecting **small recurring directional pressure before everyone else reacts**.

### Spread interpretation
The screenshots strongly imply:
- spread is not just a transaction-cost input
- spread state may itself be informative about market regime / intent / latent pressure

Practical consequence:
- log and analyze spread regimes, not just mid-price moves
- inspect whether spread widening / persistence / asymmetry precedes directional movement or better fill opportunities
- use spread behavior as part of classification, not as an afterthought

## 3.2 Implications for quoting and execution
The language around “orders trying too hard” implies:
- naive aggressive crossing may be worse than it looks
- poor quote placement can reveal urgency and reduce execution quality
- size should fit context, not just signal strength

Practical execution hypotheses:
- avoid obviously over-eager quotes that donate edge
- use context-aware sizing rather than one-size-fits-all orders
- fair value should guide quoting, but quote placement should also respect the current book mood / regime
- patience may matter; in some states, waiting a tick or quoting less aggressively may outperform rushing to cross

## 3.3 Implications for auction work
The auction hints are unusually concrete.

Likely actionable meaning:
- the final order is not just about getting filled; it can move the clearing price
- this is a **strategic optimization problem over the clearing mechanism**
- simulations should map sensitivity of final outcome to your chosen price and size
- key targets are:
  - candidate clearing-price clusters
  - local stability points
  - how much your order nudges the final clearing price
  - where order-book mass bunches up

This suggests the correct workflow is:
1. reconstruct the auction order book / standing demand-supply schedule
2. simulate candidate final orders
3. measure resulting clearing price and fill outcome
4. identify stable / recurring price zones
5. choose the final order based on payoff, not just intuition

---

# 4. Hypotheses to test (in order of usefulness)

## 4.1 Pepper Root / slow-market hypotheses
1. **Low-volatility does not mean no alpha**
   - test for short-horizon persistence / repetition in book imbalance, spread, and queue states
2. **Spread regime is predictive**
   - test whether certain spread states precede future mid-price drift, stronger fill quality, or better passive capture
3. **Lean-before-move behavior exists**
   - test whether repeated mild imbalance or one-sided quote pressure predicts short future direction
4. **Subtle regime repetition matters more than strong single-tick signals**
   - compare repeated-pattern detectors against noisy one-step predictors

## 4.2 Order-placement hypotheses
1. **Less eager quotes improve edge retention**
   - compare aggressive “lean-forward” pricing against calmer fair-relative quoting
2. **Context-matched size outperforms fixed size**
   - vary size based on spread / imbalance / inventory / urgency
3. **Small timing delays can improve quote quality**
   - if your simulator or execution model supports it, compare immediately-crossing behavior versus waiting for better setup

## 4.3 Auction hypotheses
1. **There are stable clearing-price basins**
   - simulate price/size perturbations to find prices where outcomes keep converging
2. **Your final order has leverage over the clearing price**
   - quantify the marginal impact of final price and size choice
3. **Clustered book mass identifies likely clear points**
   - inspect bunching in aggregate supply/demand curves
4. **Best auction action is not always passive participation**
   - compare “accept the expected clear” versus “strategically nudge the clear” behavior

---

# 5. What should NOT be overclaimed from these screenshots

Do **not** infer the following as hard facts from the screenshots alone:
- exact strategy type that will win the round
- exact statistical model to use
- exact relationship between spread and future returns
- exact auction clearing algorithm
- exact product taxonomy for all Round 1 products
- that Pepper Root must trend rather than mean-revert
- that aggressive orders are always bad

These prompts provide **directional guidance**, not formal proofs.

---

# 6. Suggested use in Codex prompts

When using this file to brief Codex, treat it as a soft-hint layer below official docs and local data.

Recommended phrasing:
- Use official round materials as the source of truth for rules and interface.
- Use this prompt-hints file as a source of narrative strategic clues.
- Explicitly test whether Pepper Root has subtle repeatable regimes, especially in spread and imbalance behavior.
- For auction tasks, simulate how final order price and size move the clearing outcome rather than treating the final order as passive.
- Do not import stale assumptions from older Prosperity repos.

---

# 7. Condensed competition takeaways

## For trading strategy
- Watch for **subtle** trends, not just loud ones.
- `Intarian Pepper Root` may hide exploitable structure despite appearing stable.
- Repeated mild imbalance or one-sided leaning may matter.
- Spread behavior may contain signal, not only cost.
- Slow markets may reward careful pattern recognition.

## For order placement
- Fair value is necessary but not sufficient.
- Avoid conspicuously eager pricing and size.
- Quote placement should feel context-consistent, not urgent.
- Price, size, and patience are all decision variables.

## For auction strategy
- Final order can change the clearing price.
- Simulate price/size perturbations.
- Look for bunching and recurring snap points.
- Treat the auction as an optimization problem, not a participation formality.

---

# 8. Confidence grading

## High confidence
- Pepper Root is being hinted as subtle / stable / pattern-bearing.
- Spread behavior is being flagged as meaningful.
- Over-eager orders are discouraged.
- Final auction order can affect the clearing price.
- Simulation of auction outcomes is recommended.

## Medium confidence
- The best Round 1 algotrading edge may involve subtle regime detection rather than loud trends.
- Execution quality and quote calibration may matter materially.
- Auction outcome likely has stable local basins that can be identified numerically.

## Lower confidence / needs direct testing
- Exact directionality model for Pepper Root.
- Whether trend-following or mean-reversion dominates.
- Whether the same hint also applies to other Round 1 products.
- Whether spread intention is better captured by level-1 only or deeper book features.

---

# 9. One-paragraph handoff summary
The prompt cards strongly suggest that Round 1 alpha may come less from obvious big moves and more from subtle repeated market behavior, especially in `Intarian Pepper Root`, where slow growth and predictable supply do not prevent exploitable short-horizon shifts. The most important algorithmic hint is that spread behavior may sometimes encode market intent rather than pure noise. The main execution hint is to avoid obviously eager quotes and to calibrate price and size so orders fit the current book context instead of broadcasting urgency. The main auction hint is that the final order can move the clearing price, so auction work should be simulation-driven and focus on outcome sensitivity, bunching, and stable clearing-price zones.
