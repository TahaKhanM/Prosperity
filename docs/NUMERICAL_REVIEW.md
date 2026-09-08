# Pricing and replay corrections — 8 September 2026

These are post-competition changes to reusable analysis tools. The file in
`submissions/` is unchanged. Its inlined call pricer is independent of the
Round 4 research module. Historical notes and panels are retained as recorded;
they have not been retroactively regenerated with the corrected mathematics.

## Implied volatility and deterministic limits

The old Round 4 bisection fallback changed the price at the lower endpoint when
it actually moved the upper endpoint. It could discard the root: a call generated
at 20% volatility returned 250% when Newton was disabled. The solver now maintains
an increasing price bracket throughout Newton and bisection. It returns NaN for
unbracketed quotes, expired contracts, non-finite prices and lack of convergence.
The configurable upper volatility bound remains 5.0; a quote outside that range
is not silently clamped.

For positive maturity, zero-volatility value uses the discounted strike, and the
call lower bound is `max(S - K exp(-rT), 0)`. Zero volatility is not the same as
immediate expiry when rates are nonzero. The Round 3 call module received the same
discount correction; its separate import path remains runnable. Normal tails in
the Round 4 module use `erfc` to avoid subtracting a CDF from one.

Tests force the fallback, check textbook call/put values, rate-sensitive parity,
put-to-call inversion, finite-difference Greeks, and invalid inputs. A small price
residual does not imply well-identified volatility in deep tails: vega can be
almost zero. Near-intrinsic observations still need filtering before smile fitting.

## Continuously monitored knockout put

The old down-and-in expression omitted terms from the `K > B` branch. Subtracting
it from the vanilla price and clipping at zero concealed the error: all of
S=35.1, 36, 40, 45 and 48 with K=45, B=35, T=21/365, sigma=0.2 returned zero.
The corrected S=40 price is **4.9472048283**, versus **5.0046810761** for the vanilla.

The implementation integrates the payoff against the absorbing GBM transition
density. Let `x=log(S/B)`, `y=log(S_T/B)`, `v=sigma²T`, and
`d=(r-sigma²/2)T`. On `y>0` the killed density is

```text
normal(y; x+d, v) - exp(-2dx/v) normal(y; -x+d, v).
```

Integrating `(K-B exp(y))` over `0 < y < log(K/B)` gives two truncated-normal
moments. This is algebraically equivalent to the full no-rebate down-and-out
branch in [QuantLib's analytic barrier engine](https://github.com/lballabio/QuantLib/blob/master/ql/pricingengines/barrier/analyticbarrierengine.cpp).
The implementation was derived from those moments; the tests also evaluate the
density numerically with Simpson quadrature, without using the production CDF
antiderivative. They cover spots close to the barrier, positive/negative rates,
knockout at the barrier, expiry, deterministic crossing and a remote barrier.

This model assumes constant volatility, no dividends, no previous knockout and
continuous monitoring. A puzzle monitored only at specified dates needs a
corresponding discrete-monitoring model.

A second review found that simply skipping an underflowed reflected tail was
unsafe: its multiplier can be huge. For S=40, K=45, B=35, T=1,
r=-log(40/35), sigma=0.007 the analytic evaluation overflowed; at sigma=0.0069
it silently overvalued the contract by about 0.118. Large positive image
exponents now use a standard-library adaptive Simpson fallback. The identity
`image/free = exp(-2xy/v)` expresses the killed density as a positive product;
`expm1` avoids cancellation, and integration in standard-normal coordinates
resolves a narrow low-volatility distribution. Ordinary cases retain the fast
analytic path. The fallback is slower, has an explicit convergence failure,
and is not an arbitrary-precision replacement.

The integration domain is clipped at 12 standard deviations; omitted normal
mass is below 4e-33, and the normalized-payoff Simpson tolerance is 1e-12.
Four low-volatility boundary regressions use independently calculated 80-digit
reference values. A separate 180-case high-precision grid over spots near and
far from the barrier, short/year maturities, positive/zero/negative rates and
volatilities 0.001–1 had no exceptions and maximum absolute error 5.01e-11.
This verifies that grid, not all finite floating-point parameter combinations.
Digital zero-volatility payoffs now use the forward and discount factor; chooser
deltas also handle a decision made now. Digital and knockout deltas validate
inputs and numerical step sizes; an unbreached knockout delta keeps its stencil
above the barrier. At zero volatility, call theta includes discounted-strike
decay and at-the-money forward vega uses its right derivative. Gamma at that
payoff kink, and digital delta at the deterministic exercise boundary, return
NaN rather than inventing a finite derivative. The existing half-delta convention
at an exactly at-the-money vanilla kink remains explicit. The digital is not generically insensitive
to volatility, so that earlier comment was removed.

## Replay safeguards

The replay keeps current order books available at decision time and reveals the
previous tick's market trades to the next invocation. It matches buys and sells
against visible depth and an approximate trade-print queue model. It does not
model queue cancellations, endogenous impact, fees, latency, settlement or
conversion cash flows. Nonzero conversions now fail explicitly.

Order-limit accumulation now uses a wider integer, so extreme malformed order
quantities cannot overflow the risk check. PEBBLES and SNACKPACK products use the
10-unit caps recorded in the team's Round 5 Python backtester and traders.
Unknown product limits reject orders with a diagnostic instead of assuming 100.
Other Round 5 products still require validated limit definitions.

The test suite no longer depends on a deleted `latest_trader.py` or assumes that
tutorial data are the latest available round. A controlled fixture tests artifact
creation; temporary directories test dataset selection independently of the archive.

Missing book mids now carry the last observed mark, without looking ahead.
Inventory with no historical mark fails explicitly. This prevents an absent
snapshot from valuing an open position at zero; it does not claim the stale
mark is a liquidation price. The carry integration test covers a missing
second-day mark.

## Counterparty labels and manual bids

The scanner now requires a mid at the exact requested future horizon. Missing
end-of-day/gap observations are censored: their volume is counted separately
and excluded from per-unit mark-out means. Previously a missing value could
become zero PnL in the denominator or silently shift to a farther horizon.
Custom horizons now appear in column names. The generated report describes
in-sample associations instead of declaring counterparties informed or giving
unconditional copy/fade advice.

`round3_manual_research/bids.py` gives exact uniform-grid first-bid EV and
second-bid rival-mean sensitivity. It corrects the notebook's lower-bound count,
normalization and endpoint division; the underlying reserve and allocation
assumptions remain hypotheses, not recovered official outcomes.
