# Round 3 manual bid models

The two archived notebooks explore a reserve-price bid and a second bid whose
payoff depends on opponents' mean bid. They are separate simplified calculations,
not a joint optimization of a complete bid pair. The manual challenge is
independent of the algorithmic trader.

`bid1.ipynb` enumerates integer bids under an assumed uniform reserve grid from
670 through 920 in steps of five. Its displayed "EV" omitted division by the 51
possible reserves and its count was negative at the lower boundary. The missing
normalization preserves the interior argmax but changes the interpretation of the
number. `bid2.ipynb` samples an assumed mixture of competitor bids without fixing
a random seed; it does not estimate the mixture from observed opponent choices.

The notebooks are preserved as competition-era research. The post-competition
[`bids.py`](bids.py) exposes corrected, deterministic calculations:

```bash
python3 round3_manual_research/bids.py
```

The first model computes the exact acceptance probability by enumeration. It
assumes a bid must **strictly exceed** a reserve, so equality does not win.
The second prints sensitivity to the assumed rival mean and handles a bid of
920 without a division by zero. Its output is conditional payout, excluding the
chance of receiving an allocation; do not call it total expected auction profit.
Neither calculation establishes actual competition winnings or an equilibrium
against strategic opponents. Verify the original contract's reserve distribution,
tie rules, allocation mechanism and penalty before using the model for a decision.
