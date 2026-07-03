# Round 4 hint cards — verbatim with research implications

> Source: `Data/ROUND 4 Hints.txt`. These are cinematic prompt-cards from the
> in-fiction adviser. They map onto specific research areas. Treat as
> medium-signal: they hint at the intended structure of the round, but do not
> override evidence from the data.

---

## Card 1 — "Implied Volatility and Moneyness"

> "The Velvetfruit Extract Vouchers are not just prices on a screen. They have
> structure underneath. The Black-Scholes formula lets you pull out the
> Implied Volatility embedded in each one. That number tells you what
> uncertainty the market has already priced in. Which is, honestly, more
> interesting than the price itself.
>
> Run it across all the vouchers. See how the volatility shifts across
> different strikes and timeframes. Does it move smoothly or does it get weird
> in places? Then bring in moneyness. How far each voucher's strike sits from
> the current underlying price. Plot that against your volatility figures and
> something starts to take shape.
>
> That shape is the market telling you what it thinks. Not out loud,
> obviously. Markets don't do that. But it's there if you're paying attention.
> And you know I am, even when it looks like I'm not.
>
> Don't skip this part trying to get to the exciting bit. The structure is the
> exciting bit. Or at least, it's where everything useful comes from. Which is
> basically the same thing."

**Research implication.** Build the IV(moneyness, TTE) surface using
`scripts/round4_options/build_voucher_panel.py` and `vol_surface_fit.py`
across days 1/2/3 (TTE = 7/6/5). The Round 3 alpha hunt already established
that the smile has deterministic TTE drift; revalidate on Round 4 data and
write the per-TTE coefficients to
`prosperity-research/04_signal_notes/round4/vol_surface_coeffs.csv`.

---

## Card 2 — "Positioning With IV and Moneyness"

> "So you have the structure. Good for you. Now look at it properly. Does it
> hold together or does something feel off?
>
> Because it usually does. There is almost always a voucher sitting somewhere
> it probably should not. Implying more uncertainty than everything around it.
> Or weirdly calm when it has no business being calm. Those are the
> interesting ones. Those are the ones worth staring at for an extra second.
>
> Ask yourself what the deviation means. Is the market overestimating
> uncertainty there? Underestimating it? Both happen. Both mean something
> different. The direction of the gap tells you which way the opportunity
> points, if there is one.
>
> And that is the part people rush. Finding the outlier feels like the finish
> line. It is not. It is just the beginning of the actual question, which is
> whether the deviation is real, meaningful, and worth acting on. Some
> misalignments are just noise. Some are the market being wrong in a way you
> can use. Learning to tell the difference is kind of the whole thing.
>
> Buy, sell, or don't. The structure will point you somewhere. Whether you
> trust what it is pointing at is on you."

**Research implication.** This is residual scalping, framed in the language of
the round. Per-strike `res = IV_market - IV_fit`, EMA-smoothed, traded against
a per-strike threshold; existing R3 implementation generalizes directly to
R4 — see `prosperity-research/04_signal_notes/round3/ship_now.md` (alpha B1).

---

## Card 3 — "Let's Talk Volume"

> "Okay so you found something. Maybe two somethings. Or three. Or more. Or
> whatever. Now everyone's favorite question: how much?
>
> Here is the thing about volume. It is not just a number you pick because it
> feels right. It should reflect how confident you actually are. Not how
> confident you want to be. Those are different things and most people mix
> them up constantly.
>
> If one voucher looks slightly off and another looks significantly off, those
> are not the same signal. Treating them like they are is just lazy. Scale
> your exposure to match the strength of the deviation. Bigger gap, bigger
> position. Smaller gap, smaller position. It is not complicated. It is just
> easy to ignore when you are excited about having spotted something.
>
> The other side of that, obviously, is that larger volume means larger losses
> if you are wrong. And you might be wrong. Even if your read on the
> volatility structure is good, the market does not always care about your
> timeline. Sometimes it stays weird longer than you expected. Sometimes it
> moves in a completely different direction. Annoying, but true.
>
> So be honest with yourself before you commit. How strong is the signal
> really? How much can you absorb if it doesn't play out? Volume should match
> conviction. Not optimism."

**Research implication.** Position sizing should scale with `|residual| /
σ(residual)` (per-strike z-score), not a flat slot. Cap by per-strike vega-
weighted budget so that a 3σ outlier on a low-vega strike doesn't auto-fill
to the 300-cap. Implementation lives in the inventory-risk-controller skill.

---

## Card 4 — "Anticipating Activity" (counterparty card)

> "Can we just take a moment to acknowledge how bleak it is that every single
> counterparty is named Mark? All of them. Same name, different number, zero
> personality. I don't know what's more unsettling. That someone thought that
> was acceptable, or that nobody pushed back on it.
>
> You should still watch them. Obviously. Do certain Marks show up at
> predictable moments? Do they behave the same way each time? Because
> systems, like people, tend to repeat themselves. They were trained on
> something and they keep doing that something, which is actually very
> convenient for you if you pay attention.
>
> Ask yourself what each one is doing and why. Does one resemble a market
> maker, quietly providing liquidity on a schedule? Is another a liquidity
> taker, showing up when conditions suit it? Are there larger, clumsier ones
> whose arrival you can feel before you see it? Those are the interesting
> ones. The ones that might move the room.
>
> Yes. You should act on your read of the counterparties. Let your read
> change how you operate. Where you place orders. How you interpret a sudden
> price shift. Whether a movement is signal or just noise from a Mark that
> doesn't know any better.
>
> Pattern recognition is the easy part, honestly. Most people can do that.
> The harder part is actually letting it inform your decisions instead of
> just feeling clever about having noticed something."

**Research implication.** This is the *central* Round 4 alpha card. Output of
`scripts/round4_options/counterparty_scan.py` is the core artefact:
horizon-PnL per Mark per side, plus temporal pattern bucket. Three actionable
patterns to mine for:

1. **Market-maker Mark** — high volume, near-zero horizon PnL on both sides,
   tight spread. Use as a contra-trade liquidity source (do not fade).
2. **Informed Mark** — persistent positive horizon-500 PnL on one side. Copy
   their direction when they appear in `market_trades`.
3. **Liquidity-taker Mark** — sporadic, large-quantity prints that precede
   price moves. Position ahead when their pattern fires.

See `prosperity-research/04_signal_notes/round4/counterparty_findings.md`.

---

## Card 5 — "Combining Vanillas and Exotics" (manual card)

> "Exotic options. Sure. They sound impressive. Attractive payoffs,
> interesting structures, the whole thing. And then you look a little closer
> and realize they are also sensitive to basically everything. The spot
> price. The timing. The exact path the underlying took to get there. All of
> it. Which is fine, until it isn't.
>
> So before you get too attached to your exotic position, ask yourself
> whether part of that exposure could be replicated with vanilla options.
> Calls and puts are less spectacular, yes. Deliberately so. That is actually
> the point. Less spectacular usually means a bit easier to price. It means
> it does not suddenly behave differently because the underlying took an
> unexpected detour on the way to where you thought it was going.
>
> Look at the exotic payoff on its own first. Then see what happens when you
> layer vanillas alongside it. Does the combination smooth out the extreme
> outcomes? Does it make the whole thing less dependent on one very specific
> scenario playing out perfectly? It usually does. Not always in a dramatic
> way. But enough to matter when things get weird.
>
> The goal is not to turn your exotic into a vanilla. It is to build
> something around it that does not fall apart the moment conditions shift.
> Control the exposure. Do not let the exposure control you."

**Research implication.** Three exotics shipped this round (chooser, binary
put, knockout put). For each:

- **Chooser**: replicate via `max(C, P)` decomposition (chooser ≈ call(K) +
  put(K) discounted from decision date back to spot). See
  `scripts/round4_options/exotic_pricers.py::chooser_value`.
- **Binary put**: digital — decomposes as a tight put spread `(K+ε put -
  K-ε put) / (2ε) * notional`. Vega ≈ 0; pure tail bet on `S_T < K`.
- **Knockout (down-and-out) put**: vanilla put minus rebate-paid down-and-in
  put. Closed-form available under BS (Reiner-Rubinstein); the in-repo
  `exotic_pricers.py` uses that formula.

Ladder them: short the over-priced exotic, long the vanilla replication, size
to net Greeks ≈ 0 except on the residual mispricing.

---

## Card 6 — "Choosing a Strategy for Chooser Options"

> "Okay so a chooser option has two phases and they are not the same thing.
> Like, at all. Treating them like they are is how people end up confused and
> slightly poorer than they expected.
>
> In the first phase you still get to decide whether the option becomes a
> call or a put. That flexibility is worth something. An actual measurable
> something. Ask yourself whether you could approximate that exposure using
> vanilla options. A combination of calls and puts might get you close enough
> to give you a useful reference point for what that optionality is actually
> worth right now. Which is good to know before you do anything else.
>
> Then the decision window closes. And everything changes. The option type
> gets fixed and suddenly you are not dealing with open-ended flexibility
> anymore. You are dealing with a directional position that has a very
> specific opinion about where the underlying is going. That is a completely
> different situation and it needs a completely different approach.
>
> So manage the two phases separately. What works in the first phase might
> not serve you well in the second. The transition is the part most people
> gloss over because it feels like a formality. It is not. It is the whole
> thing."

**Research implication.** A chooser is a call + a put with the same strike
and the put discounted from the choice date `T_c` to the chooser's expiry
`T`:

```
Chooser(K, T_c, T) ≈ C(S, K, T) + P(S, K e^{-r(T - T_c)}, T_c)
```

(With `r = 0` in Prosperity, the put strike collapses to `K`.) For our card,
K = 50 XIRECS, T = 21 days, T_c = 14 days. Use the BS-based decomposition for
fair value and compare against the on-screen offer. The auto-conversion rule
("becomes whichever side is in the money at the decision point") aligns with
the standard simple-chooser identity, so the decomposition is exact under BS.
