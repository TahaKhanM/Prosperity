"""Round 3 local test variant based on round3_v3.

This file intentionally preserves round3_v3 behavior. It exists as a quick
pipeline test for building and backtesting a new candidate from the locally
best-performing historical Round 3 trader.

Local baseline:
  round3_v3.py: +142,254.00 over round3 day_0..day_2 in the Rust backtester.

Note: this wrapper imports the baseline trader and is meant for local testing,
not direct hosted submission. For hosted submission, use a self-contained
single-file trader such as round3_v3.py itself or copy its full contents.
"""

from traders.Round3.candidates.round3_v3 import Trader as _Round3V3Trader


class Trader(_Round3V3Trader):
    """Behavior-identical local test wrapper around the round3_v3 Trader."""

