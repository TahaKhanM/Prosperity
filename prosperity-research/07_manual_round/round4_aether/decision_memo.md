# Round 4 manual decision memo — Aether Crystal options

> Status: TEMPLATE. Live Manual Challenge prices have not yet been observed.
> Update this memo each time the Manual Challenge window in the Prosperity UI
> shows new bid / ask / volume.

## 1. Observed inputs (live)

- Aether Crystal **spot** S = `<TODO>` XIRECS.
- Vanilla calls: list strikes / bids / asks / available volume.
- Vanilla puts:  list strikes / bids / asks / available volume.
- Exotics:
  - **Chooser** (K=50, expiry 21d, decision day 14): bid=`<TODO>`, ask=`<TODO>`, vol=`<TODO>`.
  - **Binary put** (K=40, expiry 21d, payoff 10): bid=`<TODO>`, ask=`<TODO>`, vol=`<TODO>`.
  - **Knockout put** (K=45, B=35, expiry 21d): bid=`<TODO>`, ask=`<TODO>`, vol=`<TODO>`.

## 2. Calibration

| Step | Value | Notes |
|---|---|---|
| Most-trustworthy vanilla | `<TODO>` | Pick the longest-dated, near-ATM vanilla with the tightest spread. |
| σ implied from that vanilla (mid) | `<TODO>` | Newton on `bs.implied_vol_call` or `implied_vol_put`. |
| σ cross-check on a 2nd strike | `<TODO>` | Should agree to within ~0.02 absolute. If not, the vol surface is itself an alpha. |
| Year basis | 365 | Prosperity convention (Round 3 winner Timo). |
| Risk-free rate | 0 | No stated rate. |

## 3. Fair value table

Run:

```sh
python3 prosperity_rust_backtester/scripts/round4_options/exotic_pricers.py \
    --spot <S> --sigma <sigma>
```

| Contract | Market mid | BS fair | Gap (mid − fair) | Vega | Delta | Notes |
|---|---|---|---|---|---|---|
| Chooser K=50 | `<TODO>` | `<TODO>` | `<TODO>` | `<TODO>` | `<TODO>` | Replicate as `Call(50, 21d) + Put(50, 14d)` under r=0. |
| Binary put K=40 | `<TODO>` | `<TODO>` | `<TODO>` | ≈ 0 | `<TODO>` | Replicate as `(Put(40+ε) − Put(40−ε)) / 2ε × 10`. |
| Knockout put K=45, B=35 | `<TODO>` | `<TODO>` | `<TODO>` | `<TODO>` | `<TODO>` | Bounded above by vanilla Put(45). If quote > vanilla Put(45), risk-free arb. |

## 4. Replication plan

For each over-priced exotic:
- **Chooser over-priced**: sell chooser, buy `Call(50, 21d)` and `Put(50, 14d)` in same notional. Net delta ≈ 0.
- **Binary put over-priced**: sell digital, buy tight put-spread `(Put(40+ε) − Put(40−ε))` scaled by `10/(2ε)`.
- **Knockout put over-priced vs. vanilla**: short knockout, long vanilla put (K=45). Direct arb.

For each under-priced exotic:
- Reverse the trade if the same vanillas are available on the bid side.

## 5. Position sizing

Per the Round 4 hint card "Let's Talk Volume":

> Bigger gap, bigger position. Smaller gap, smaller position.

Score each opportunity by `|gap| / σ_market`. Allocate budget proportionally,
capped by available volume per contract.

Minimum-edge filter: do not trade if `|gap| < 0.10` (in XIRECS) — execution
cost will eat the edge.

## 6. Chosen positions

| Contract | Direction | Size | Reasoning |
|---|---|---|---|
| `<TODO>` | `<long/short>` | `<units>` | `<TODO>` |

## 7. Worst-case PnL

For each leaf scenario `S_T ∈ {25, 30, 35, 40, 45, 50, 55, 60, 65, 70}`,
compute the package payoff. Path scenarios for the knockout: `min(S_t)` over
the 21 days < 35 vs. ≥ 35.

| `S_T` | Knockout path? | Chooser payoff | Binary put payoff | Knockout payoff | Vanilla legs payoff | **Net PnL** |
|---|---|---|---|---|---|---|
| 25 | breached | … | 10 | 0 | … | … |
| 30 | breached | … | 10 | 0 | … | … |
| 35 | breached @ 35 | … | 10 | 0 | … | … |
| 40 | OK (assume) | … | 10 | 5 | … | … |
| 45 | OK | … | 0 | 0 | … | … |
| 50 | OK | … | 0 | 0 | … | … |
| 55 | OK | … | 0 | 0 | … | … |
| 60 | OK | 10 | 0 | 0 | … | … |
| 65 | OK | 15 | 0 | 0 | … | … |
| 70 | OK | 20 | 0 | 0 | … | … |

Max absolute drawdown across the table → headline risk number.

## 8. Invalidation test

Resubmit if any of the following happens:
- Aether Crystal spot moves > 5 % during the round.
- A vanilla strike's bid/ask shifts by > 1 XIRECS.
- The chooser auto-conversion is announced before the decision date (would
  mean the option is treated as a vanilla immediately).
- Available volume on a chosen contract drops to < 50 % of the planned size.

## 9. Submission log

Track every adjustment here so that the *last* one is auditable:

| Time | Spot used | σ used | Submitted positions | Notes |
|---|---|---|---|---|
| `<TODO>` | `<TODO>` | `<TODO>` | `<TODO>` | first draft |

The **final** entry counts. Do not forget to lock in the version you actually
want before the round timer expires.
