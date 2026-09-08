"""Deterministic checks of the assumptions in the archived Round 3 notebooks.

This is an assumption model, not a recovered official result. Reserve prices
are uniform on {670,675,...,920}; a first bid must strictly exceed the reserve.
The second-bid function is the notebook's conditional payoff, not a joint
auction EV. See README.md for the distinction.
"""
import math

LOW, HIGH, STEP = 670, 920, 5
RESERVES = tuple(range(LOW, HIGH + 1, STEP))


def first_bid_ev(bid: float) -> float:
    if not math.isfinite(bid) or not LOW <= bid <= HIGH:
        raise ValueError('bid must be finite and in [670,920]')
    accepted = sum(reserve < bid for reserve in RESERVES)
    return accepted / len(RESERVES) * (HIGH - bid)


def second_bid_payoff(bid: float, opponent_mean: float) -> float:
    """Conditional payout given an assumed rival mean; excludes award odds."""
    if not all(math.isfinite(x) and LOW <= x <= HIGH for x in (bid, opponent_mean)):
        raise ValueError('bid and opponent mean must be finite and in [670,920]')
    spread = HIGH - bid
    if spread == 0:
        return 0.0
    if bid > opponent_mean:
        return spread
    return spread * ((HIGH - opponent_mean) / spread)**3


def main():
    bids = range(LOW,HIGH+1)
    best = max(bids,key=first_bid_ev)
    print(f'Uniform-grid first-bid model: best integer bid={best}, EV={first_bid_ev(best):.6f}')
    print('Second-bid sensitivity (conditional payoff; assumed rival mean):')
    for rival_mean in [910,914,916,918,919,920]:
        best = max(range(LOW,HIGH+1),key=lambda bid:second_bid_payoff(bid,rival_mean))
        print(f'  mean={rival_mean}: best integer bid={best}, payoff={second_bid_payoff(best,rival_mean):.4f}')


if __name__=='__main__':main()
